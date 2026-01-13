# Start New Research Project

Launch the research elicitation agent to guide you through setting up a new research project.

## What This Does

The research elicitation agent will:
1. Ask targeted questions to understand your research goals
2. Help you configure verticals, personas, and research type
3. Guide you on appropriate context inclusion
4. Create isolated run directory with proper configuration
5. Estimate costs and timeline
6. Provide launch commands

## Execution

Invoke the research-elicitation agent with user's initial request (if any):

```
User request: $ARGUMENTS
```

The agent will guide the conversation from there.

## Example Usage

```
/research-new healthcare market discovery
/research-new validate our financial services messaging
/research-new
```

If no arguments provided, agent will start with open-ended discovery questions.
