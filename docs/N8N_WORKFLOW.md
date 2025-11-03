# n8n Workflow Integration Guide

## Overview

This guide explains how to integrate the code review system with n8n for automated GitLab merge request reviews, including workflow design, LangChain Code Node usage, and troubleshooting.

---

## Architecture

```
GitLab MR Event (Webhook)
    ↓
n8n Workflow Trigger
    ↓
┌─────────────────────────────────────┐
│ 1. Validate MR (LangChain Code Node)│
│    - Check JIRA ticket              │
│    - Validate description           │
│    - Score completeness             │
└────────────────┬────────────────────┘
                 ↓
         [Validation Failed?]
                 ↓ No
┌─────────────────────────────────────┐
│ 2. Call Review API                  │
│    - POST /api/v1/review            │
│    - Include validation context     │
└────────────────┬────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│ 3. Process Results                  │
│    - Post summary to GitLab         │
│    - Create fix MRs if needed       │
│    - Notify team                    │
└─────────────────────────────────────┘
```

---

## Workflow Setup

### Prerequisites

- n8n instance (self-hosted or cloud)
- GitLab webhook access
- Review API accessible from n8n
- (Optional) Jira API access
- (Optional) Confluence API access

---

## Workflow Configuration

### Node 1: GitLab Webhook Trigger

**Node Type**: Webhook  
**Purpose**: Receive merge request events from GitLab

**Configuration**:
```json
{
  "httpMethod": "POST",
  "path": "code-review-webhook",
  "responseMode": "immediate",
  "responseData": "{ \"status\": \"received\" }"
}
```

**GitLab Webhook Settings**:
- URL: `https://n8n.example.com/webhook/code-review-webhook`
- Trigger: Merge Request events
- Events: Open, Update
- SSL verification: Enabled
- Secret token: `your-webhook-secret`

---

### Node 2: Filter MR Events

**Node Type**: IF  
**Purpose**: Only process relevant MR events

**Configuration**:
```javascript
// Condition
$json.body.object_attributes.action === 'open' || 
$json.body.object_attributes.action === 'update'
```

---

### Node 3: Extract MR Data

**Node Type**: Code Node (JavaScript)  
**Purpose**: Extract and structure MR information

**Code**:
```javascript
const mr = $json.body.object_attributes;
const project = $json.body.project;
const user = $json.body.user;

return {
  project_id: project.id,
  project_name: project.name,
  mr_iid: mr.iid,
  mr_id: mr.id,
  title: mr.title,
  description: mr.description || '',
  source_branch: mr.source_branch,
  target_branch: mr.target_branch,
  author: {
    username: user.username,
    name: user.name,
    email: user.email
  },
  web_url: mr.url,
  created_at: mr.created_at,
  updated_at: mr.updated_at
};
```

---

### Node 4: Validate MR with LangChain Code Node

**Node Type**: LangChain Code Node  
**Purpose**: Validate MR completeness and extract JIRA ticket

**Configuration**:
```javascript
// Import LangChain modules
const { ChatOpenAI } = require('@langchain/openai');
const { PromptTemplate } = require('@langchain/core/prompts');

// Get MR data from previous node
const title = $json.title;
const description = $json.description;

// Create prompt template
const promptTemplate = PromptTemplate.fromTemplate(`
Analyze this GitLab merge request for completeness:

Title: {title}
Description: {description}

Validate:
1. JIRA ticket reference in title (format: PROJECT-123)
2. Description length (minimum 50 characters)
3. No placeholder text (TODO, TBD, etc.)

Return JSON:
{{
  "is_valid": true/false,
  "errors": ["error1", "error2"],
  "jira_ticket": "PROJECT-123" or null,
  "completeness_score": 0-100
}}
`);

// Initialize LLM
const llm = new ChatOpenAI({
  modelName: 'gpt-4',
  temperature: 0,
  openAIApiKey: process.env.OPENAI_API_KEY
});

// Create chain
const chain = promptTemplate.pipe(llm);

// Execute
const result = await chain.invoke({
  title: title,
  description: description
});

// Parse response
const validation = JSON.parse(result.content);

return {
  ...validation,
  original_title: title,
  original_description: description
};
```

---

### Node 5: Check Validation Result

**Node Type**: IF  
**Purpose**: Branch based on validation

**Configuration**:
```javascript
// Condition
$json.is_valid === true && $json.completeness_score >= 70
```

**True Output**: Continue to review  
**False Output**: Post validation errors and stop

---

### Node 6: Post Validation Errors (if validation failed)

**Node Type**: HTTP Request  
**Purpose**: Post validation errors to GitLab MR

**Configuration**:
```json
{
  "method": "POST",
  "url": "={{ $('Extract MR Data').item.json.web_url }}/notes",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "gitLabApi",
  "sendBody": true,
  "bodyParameters": {
    "body": "## ❌ Merge Request Validation Failed\n\n{{ $json.errors.join('\\n') }}\n\n**Completeness Score**: {{ $json.completeness_score }}/100\n\nPlease address these issues before requesting code review."
  }
}
```

---

### Node 7: Load Custom Rules (Optional)

**Node Type**: HTTP Request  
**Purpose**: Load project-specific or Confluence rules

**For Confluence**:
```json
{
  "method": "GET",
  "url": "https://confluence.company.com/rest/api/content/{{ $env.CONFLUENCE_PAGE_ID }}?expand=body.storage",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "confluenceApi",
  "options": {
    "cache": {
      "enabled": true,
      "ttl": 3600
    }
  }
}
```

**Extract Rules**:
```javascript
// Code Node after HTTP Request
const content = $json.body.storage.value;

// Extract markdown sections
const sections = {
  error_detection: extractSection(content, 'Error Detection'),
  best_practices: extractSection(content, 'Best Practices'),
  security: extractSection(content, 'Security')
};

function extractSection(content, sectionName) {
  const regex = new RegExp(`## ${sectionName}([\\s\\S]*?)(?=##|$)`, 'i');
  const match = content.match(regex);
  return match ? match[1].trim() : '';
}

return {
  confluence_rules: sections
};
```

---

### Node 8: Call Review API

**Node Type**: HTTP Request  
**Purpose**: Trigger code review

**Configuration**:
```json
{
  "method": "POST",
  "url": "http://review-api:8000/api/v1/review",
  "authentication": "none",
  "sendHeaders": true,
  "headerParameters": {
    "Content-Type": "application/json"
  },
  "sendBody": true,
  "bodyParameters": {
    "agent": "CLINE",
    "review_types": ["ALL"],
    "project_id": "={{ $('Extract MR Data').item.json.project_id }}",
    "merge_request_iid": "={{ $('Extract MR Data').item.json.mr_iid }}",
    "language": "java",
    "jira_context": "={{ $('Validate MR').item.json.jira_ticket }}",
    "confluence_rules": "={{ $('Load Custom Rules').item.json.confluence_rules }}"
  },
  "options": {
    "timeout": 600000
  }
}
```

---

### Node 9: Process Review Results

**Node Type**: Code Node  
**Purpose**: Format review results for GitLab

**Code**:
```javascript
const results = $json;

// Count issues by severity
const critical = results.issues.filter(i => i.severity === 'CRITICAL').length;
const high = results.issues.filter(i => i.severity === 'HIGH').length;
const medium = results.issues.filter(i => i.severity === 'MEDIUM').length;
const low = results.issues.filter(i => i.severity === 'LOW').length;

// Determine overall status
let status = '✅';
let statusText = 'PASSED';
if (critical > 0) {
  status = '❌';
  statusText = 'FAILED';
} else if (high > 0) {
  status = '⚠️';
  statusText = 'WARNING';
}

// Format markdown comment
const comment = `
## ${status} Code Review Results - ${statusText}

**Review Type**: ${results.review_type}
**CLI Agent**: ${results.agent}
**Files Analyzed**: ${results.summary.files_analyzed}

### Issue Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | ${critical} |
| 🟠 High | ${high} |
| 🟡 Medium | ${medium} |
| 🔵 Low | ${low} |
| **Total** | **${critical + high + medium + low}** |

### Critical Issues

${results.issues
  .filter(i => i.severity === 'CRITICAL')
  .map(issue => `
#### ${issue.category}

**File**: \`${issue.file}\`  
**Line**: ${issue.line}

**Issue**: ${issue.message}

\`\`\`java
${issue.code_snippet}
\`\`\`

**Suggestion**: ${issue.suggestion}

${issue.auto_fixable ? '✨ *Auto-fixable*' : '⚙️ *Manual fix required*'}
`)
  .join('\\n---\\n')}

### Actions Taken

${results.documentation_committed ? '- ✅ Documentation improvements committed to source branch' : ''}
${results.fix_mr_created ? `- ✅ Fix MR created: ${results.fix_mr_url}` : ''}
${results.refactoring_mr_created ? `- ✅ Refactoring MR created: ${results.refactoring_mr_url}` : ''}

---

*Powered by AI Code Review System v2.0.0*
`;

return {
  comment: comment,
  status: statusText,
  critical_count: critical,
  high_count: high,
  fix_mr_url: results.fix_mr_url,
  refactoring_mr_url: results.refactoring_mr_url
};
```

---

### Node 10: Post Review Comment to GitLab

**Node Type**: HTTP Request  
**Purpose**: Post formatted results as MR comment

**Configuration**:
```json
{
  "method": "POST",
  "url": "={{ $env.GITLAB_URL }}/api/v4/projects/={{ $('Extract MR Data').item.json.project_id }}/merge_requests/={{ $('Extract MR Data').item.json.mr_iid }}/notes",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "gitLabApi",
  "sendHeaders": true,
  "headerParameters": {
    "Private-Token": "={{ $env.GITLAB_TOKEN }}"
  },
  "sendBody": true,
  "bodyParameters": {
    "body": "={{ $json.comment }}"
  }
}
```

---

### Node 11: Notify Team (Optional)

**Node Type**: Slack / Email / Webhook  
**Purpose**: Notify team of critical issues

**Condition**: Only if critical issues found

**Slack Example**:
```json
{
  "channel": "#code-review-alerts",
  "text": "🚨 Critical issues found in MR !{{ $('Extract MR Data').item.json.mr_iid }}",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*MR*: {{ $('Extract MR Data').item.json.title }}\n*Author*: {{ $('Extract MR Data').item.json.author.name }}\n*Critical Issues*: {{ $json.critical_count }}\n*URL*: {{ $('Extract MR Data').item.json.web_url }}"
      }
    }
  ]
}
```

---

## Advanced Scenarios

### Scenario 1: Conditional Review Types

Only run security audit for backend changes:

**Node**: Code Node (before Review API call)

```javascript
const mrData = $('Extract MR Data').item.json;

// Determine review types based on changes
let reviewTypes = ['ERROR_DETECTION', 'BEST_PRACTICES'];

// If backend files changed, add security audit
const changedFiles = mrData.changes || [];
const hasBackendChanges = changedFiles.some(file => 
  file.path.includes('src/main/java/') && 
  (file.path.includes('controller') || file.path.includes('security'))
);

if (hasBackendChanges) {
  reviewTypes.push('SECURITY_AUDIT');
}

// If database files changed, add database optimization
const hasDatabaseChanges = changedFiles.some(file =>
  file.path.includes('repository') || 
  file.path.includes('entity') ||
  file.path.includes('migration')
);

if (hasDatabaseChanges) {
  reviewTypes.push('DATABASE_OPTIMIZATION');
}

return {
  review_types: reviewTypes,
  has_backend_changes: hasBackendChanges,
  has_database_changes: hasDatabaseChanges
};
```

---

### Scenario 2: JIRA Integration

Fetch JIRA task details and pass as context:

**Node**: HTTP Request

```json
{
  "method": "GET",
  "url": "https://jira.company.com/rest/api/3/issue/={{ $('Validate MR').item.json.jira_ticket }}",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "jiraApi"
}
```

**Extract Context**:
```javascript
const issue = $json;

return {
  jira_context: {
    ticket: issue.key,
    summary: issue.fields.summary,
    description: issue.fields.description,
    acceptance_criteria: extractAcceptanceCriteria(issue.fields.description),
    issue_type: issue.fields.issuetype.name,
    priority: issue.fields.priority.name
  }
};

function extractAcceptanceCriteria(description) {
  const regex = /Acceptance Criteria:([\\s\\S]*?)(?=\\n\\n|$)/i;
  const match = description.match(regex);
  return match ? match[1].trim() : '';
}
```

---

### Scenario 3: Scheduled Re-review

Re-review open MRs daily to catch new issues:

**Trigger**: Schedule (Cron)  
**Cron**: `0 9 * * *` (daily at 9 AM)

**Workflow**:
1. List open MRs (GitLab API)
2. Filter MRs older than 24 hours
3. For each MR, trigger review
4. Post update comment with new findings

---

## Error Handling

### Timeout Handling

**Node**: Code Node (after Review API call)

```javascript
// Check if review timed out
if ($json.error && $json.error.includes('timeout')) {
  return {
    error: true,
    message: 'Review timed out. Retrying with reduced scope...',
    retry: true,
    reduced_review_types: ['ERROR_DETECTION', 'SECURITY_AUDIT']
  };
}

return { error: false };
```

---

### Retry Logic

**Node**: IF (check retry flag)

**True Branch**: Call Review API again with reduced scope

---

### Error Notification

**Node**: HTTP Request (Slack webhook)

```json
{
  "method": "POST",
  "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "sendBody": true,
  "bodyParameters": {
    "text": "⚠️ Code review failed for MR !{{ $('Extract MR Data').item.json.mr_iid }}: {{ $json.error }}"
  }
}
```

---

## Testing Workflow

### Test with Sample Payload

1. **Capture real webhook payload**:
```bash
# In n8n, enable "Wait for test event" on webhook node
# Trigger real MR event in GitLab
# Copy captured payload
```

2. **Create test workflow**:
- Use "Manual Trigger" instead of Webhook
- Paste sample payload in Code Node
- Run workflow manually

3. **Verify each node**:
- Check node outputs
- Validate API calls
- Confirm GitLab comments posted

---

## Monitoring

### Workflow Execution Logs

Access n8n execution logs:
- Navigate to workflow
- Click "Executions"
- Filter by status (Success/Error/Waiting)

### Key Metrics

- **Success Rate**: % of successful reviews
- **Average Duration**: Time from trigger to completion
- **Error Rate**: % of failed executions
- **Timeout Rate**: % of reviews timing out

---

## Best Practices

### 1. Use Environment Variables

Store sensitive data in n8n environment variables:
- `GITLAB_TOKEN`
- `GITLAB_URL`
- `REVIEW_API_URL`
- `OPENAI_API_KEY`
- `CONFLUENCE_API_TOKEN`

### 2. Implement Caching

Cache Confluence rules (1 hour TTL) to reduce API calls

### 3. Handle Rate Limits

Add delay nodes between GitLab API calls if needed

### 4. Log Important Events

Use "Set" node to log key events for debugging:
```json
{
  "event": "review_completed",
  "mr_id": "={{ $('Extract MR Data').item.json.mr_iid }}",
  "issues_found": "={{ $json.summary.total_issues }}",
  "timestamp": "={{ $now.toISO() }}"
}
```

### 5. Separate Workflows

Consider separate workflows for:
- Initial MR review
- Re-review on updates
- Scheduled reviews
- Emergency security audits

---

## Troubleshooting

### Issue: Webhook Not Triggering

**Check**:
1. GitLab webhook configured correctly?
2. n8n webhook URL accessible?
3. SSL certificate valid?
4. Webhook secret matches?

**Debug**:
```bash
# Test webhook manually
curl -X POST https://n8n.example.com/webhook/code-review-webhook \
  -H "Content-Type: application/json" \
  -H "X-Gitlab-Token: your-secret" \
  -d @sample-payload.json
```

---

### Issue: LangChain Code Node Fails

**Common Causes**:
- Missing API key
- Rate limit exceeded
- Invalid JSON parsing

**Solution**:
```javascript
// Add error handling
try {
  const result = await chain.invoke({...});
  const parsed = JSON.parse(result.content);
  return parsed;
} catch (error) {
  console.error('LangChain error:', error);
  return {
    is_valid: false,
    errors: ['Validation service unavailable'],
    jira_ticket: null,
    completeness_score: 0
  };
}
```

---

### Issue: Review API Timeout

**Solutions**:
1. Increase HTTP Request timeout:
```json
{
  "options": {
    "timeout": 900000  // 15 minutes
  }
}
```

2. Use webhook mode (not implemented yet):
- Review API starts async review
- Calls n8n webhook when complete

---

## References

- [n8n Documentation](https://docs.n8n.io/)
- [LangChain JS Documentation](https://js.langchain.com/docs/)
- [GitLab Webhooks](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)
- [GitLab API](https://docs.gitlab.com/ee/api/)
- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)

---

**Last Updated**: 2025-11-03  
**Version**: 2.0.0


