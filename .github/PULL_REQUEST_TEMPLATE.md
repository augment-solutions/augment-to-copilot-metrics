# Pull Request Template

## PR Title Format
`[Phase X] Brief description of changes`

Example: `[Phase 2] Implement API token authentication layer`

---

## Description

### What does this PR do?
<!-- Provide a clear description of what this PR accomplishes -->

### Why is this change needed?
<!-- Explain the motivation and context for this change -->

### Related Issues/Tasks
<!-- Link to related issues, tasks, or planning documents -->
- Relates to Phase X in docs/IMPLEMENTATION_PLAN.md
- Addresses task: [Task name]

---

## Changes Made

### New Files
<!-- List new files created -->
- [ ] `path/to/new/file.py` - Description

### Modified Files
<!-- List files modified -->
- [ ] `path/to/modified/file.py` - What changed

### Deleted Files
<!-- List files deleted -->
- [ ] `path/to/deleted/file.py` - Why deleted

---

## Testing

### How to Test
<!-- Step-by-step instructions for testing these changes -->

1. Step 1
2. Step 2
3. Expected result

### Test Coverage
<!-- Describe test coverage -->
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

### Test Results
<!-- Paste test output or screenshots -->
```
# Test output here
```

---

## Documentation

- [ ] README.md updated (if needed)
- [ ] Docstrings added/updated
- [ ] CHANGELOG.md updated
- [ ] Architecture docs updated (if needed)

---

## Checklist

### Code Quality
- [ ] Code follows project style guidelines
- [ ] Type hints added where appropriate
- [ ] No hardcoded values (uses config)
- [ ] Error handling implemented
- [ ] Logging added for debugging

### Testing
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Edge cases covered
- [ ] No regressions introduced

### Review
- [ ] Self-reviewed the code
- [ ] Comments added for complex logic
- [ ] No debugging code left in
- [ ] No merge conflicts

### Security
- [ ] No secrets or tokens committed
- [ ] Sensitive data properly handled
- [ ] Input validation implemented

---

## Screenshots/Examples
<!-- If applicable, add screenshots or example output -->

---

## Breaking Changes
<!-- List any breaking changes and migration steps -->
- [ ] No breaking changes
- [ ] Breaking changes (describe below):

---

## Deployment Notes
<!-- Any special deployment considerations -->

---

## Questions for Reviewers
<!-- Specific questions or areas where you'd like feedback -->

1. Question 1
2. Question 2

---

## Reviewer Notes
<!-- For reviewers to add their feedback -->

### Review Checklist
- [ ] Code is clear and maintainable
- [ ] Tests are comprehensive
- [ ] Documentation is complete
- [ ] No security concerns
- [ ] Approved for merge
