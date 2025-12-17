# Agent Guidelines

This document outlines the best practices and rules that all agents should follow when working on this codebase.

## Core Principles

### 1. Minimal Intervention
**Do not apply any change that is not needed.**
- Do not edit code that was not requested to edit
- Do not do what is not explicitly told
- Only modify files and code sections that are directly related to the requested task
- Preserve existing functionality unless explicitly asked to change it

### 2. Simplicity First
**Keep it simple. The simplest solution is always the best one.**
- Try to keep your interventions minimal
- Do not go complex at once, go by steps
- Prefer straightforward implementations over elaborate solutions
- If a simple approach works, use it. Complexity can be added later if needed

### 3. Clarification and Review
**Ask for clarification when needed. Discuss changes before applying them.**
- When requirements are unclear or ambiguous, ask for clarification
- Review what you are about to apply before making changes
- Discuss significant changes or architectural decisions before implementation
- Confirm understanding of the task before proceeding

### 4. Documentation Standards
**Add documentation and parameter hints. Do not add redundant verbosity.**
- Document functions, classes, and complex logic with clear docstrings
- Add type hints to function parameters and return values
- Include parameter descriptions where helpful
- Avoid redundant comments that simply restate what the code does
- Keep documentation concise and meaningful

### 5. File Management
**Avoid creating unnecessary files. Prefer refactoring existing files.**
- Do not create new files when functionality can be added to existing ones
- When testing or experimenting, reuse existing test files instead of creating new ones
- Only create new files when there is a clear separation of concerns or module boundary
- Keep the file structure clean and minimal
- If refactoring, apply changes to the same file for clarity

## Implementation Guidelines

### Before Making Changes
1. Understand the full scope of the request
2. Identify which files need to be modified
3. Review existing code patterns and conventions
4. Ask questions if anything is unclear

### During Implementation
1. Make minimal, focused changes
2. Follow existing code style and patterns
3. Test your changes if possible
4. Keep changes isolated to the requested functionality

### After Making Changes
1. Verify that only requested changes were made
2. Ensure no unrelated code was modified
3. Confirm that existing functionality remains intact

## Examples

### ✅ Good Practice
- User asks: "Add a function to send email"
- Agent: Creates only the email sending function, adds minimal docstring and type hints
- Result: Clean, focused addition

### ❌ Bad Practice
- User asks: "Add a function to send email"
- Agent: Refactors entire email module, adds extensive comments, changes unrelated functions
- Result: Unnecessary changes, potential bugs

---

*This document should be updated as new guidelines are established.*

