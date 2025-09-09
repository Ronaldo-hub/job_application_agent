# Job Application Agent Workflow

Generated: 2025-09-09 19:59:02

## LangGraph Workflow Overview

```
START → scan_gmail → search_api_jobs → parse_jobs
                        ↓                    ↓
                 parse_resume ← analyze_job_fit
                        ↓
                 generate_resumes → audit_resumes
                        ↓
                 select_documents → suggest_courses
                        ↓
                 send_emails → discord_notifications → END
```

## Node Descriptions

### 1. scan_gmail
- **Purpose**: Scan Gmail for job-related emails using OAuth
- **Status**: ❌ Failed (OAuth not configured)
- **Output**: job_emails list

### 2. search_api_jobs
- **Purpose**: Search multiple job APIs for opportunities
- **Status**: ⚠️ Partial (40% APIs configured)
- **Output**: api_jobs list

### 3. parse_jobs
- **Purpose**: Parse job emails using spaCy NLP
- **Status**: ❌ Failed (no emails to parse)
- **Output**: parsed_jobs list

### 4. parse_resume
- **Purpose**: Load and parse master resume
- **Status**: ✅ Success
- **Output**: parsed_resume dict

### 5. analyze_job_fit
- **Purpose**: Calculate fit scores using TF-IDF
- **Status**: ⚠️ Partial (limited job data)
- **Output**: skill_gaps list

### 6. generate_resumes
- **Purpose**: Generate ATS-optimized resumes
- **Status**: ❌ Failed (no high-fit jobs)
- **Output**: generated_resumes list

### 7. audit_resumes
- **Purpose**: Audit resumes using Llama 3.1 8B
- **Status**: ❌ Failed (no resumes to audit)
- **Output**: audited_resumes list

### 8. suggest_courses
- **Purpose**: Generate course recommendations
- **Status**: ✅ Success
- **Output**: course_suggestions dict

### 9. send_emails
- **Purpose**: Send resumes via SMTP
- **Status**: ❌ Not implemented (Issue #5)
- **Output**: sent_emails list

### 10. discord_notifications
- **Purpose**: Send Discord notifications
- **Status**: ❌ Failed (no content to notify)
- **Output**: discord_notifications list

