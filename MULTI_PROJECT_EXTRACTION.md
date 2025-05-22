# Multi-Project and Group Extraction in GitLab RAG

This document provides instructions for extracting data from multiple GitLab projects and groups.

## Overview

The GitLab RAG application now supports extracting data from:
- Multiple specific project IDs
- All projects within specified groups
- Epics from multiple groups

## Command Line Usage

### Extract from Multiple Projects

To extract data from multiple specific projects, use a comma-separated list of project IDs:

```bash
python main.py --extract --project-id "12345,67890,54321"
```

### Extract from All Projects in Groups

To extract data from all projects within specific groups:

```bash
python main.py --extract --group-projects-id "12345,67890"
```

This will:
1. Find all projects in the specified groups
2. Extract data from each project automatically

### Extract Epics from Multiple Groups

To extract epics from multiple groups:

```bash
python main.py --extract --group-id "12345,67890"
```

### Combined Extraction

You can combine these approaches:

```bash
# Extract from specific projects AND all projects in groups
python main.py --extract --project-id "12345,67890" --group-projects-id "54321,98765"

# Extract from specific projects AND epics from groups
python main.py --extract --project-id "12345,67890" --group-id "54321,98765"

# Extract everything
python main.py --extract --project-id "12345,67890" --group-id "54321,98765" --group-projects-id "13579,24680"
```

## Processing Multiple Projects

After extraction, you can process all extracted projects:

```bash
python main.py --process
```

The system will automatically process all projects that were extracted in the previous step.

## Complete Pipeline for Multiple Projects

To run the complete pipeline for multiple projects:

```bash
python main.py --all --project-id "12345,67890" --group-id "54321,98765" --group-projects-id "13579,24680"
```

## Error Handling

- If a project or group ID is invalid, the system will log an error and continue with the valid IDs
- If no valid projects are found, the system will exit with an error message
- Each extraction operation is isolated, so failures in one project won't affect others

## Storage Considerations

When extracting from multiple projects:
- Each project's data is stored separately in blob storage with the project ID in the filename
- The chunking process combines data from all projects into a single file
- The embedding and indexing processes work on the combined data

## Performance Considerations

- Extracting from many projects or large groups may take significant time
- Consider extracting projects in batches if you have a very large number of projects
