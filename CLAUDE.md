# Claude Code Configuration - SPARC Development Environment

## 🚨 CRITICAL: CONCURRENT EXECUTION & FILE MANAGEMENT

**ABSOLUTE RULES**:
1. ALL operations MUST be concurrent/parallel in a single message
2. **NEVER save working files, text/mds and tests to the root folder**
3. ALWAYS organize files in appropriate subdirectories
4. **USE CLAUDE CODE'S TASK TOOL** for spawning agents concurrently, not just MCP

### ⚡ GOLDEN RULE: "1 MESSAGE = ALL RELATED OPERATIONS"

**MANDATORY PATTERNS:**
- **TodoWrite**: ALWAYS batch ALL todos in ONE call (5-10+ todos minimum)
- **Task tool (Claude Code)**: ALWAYS spawn ALL agents in ONE message with full instructions
- **File operations**: ALWAYS batch ALL reads/writes/edits in ONE message
- **Bash commands**: ALWAYS batch ALL terminal operations in ONE message
- **Memory operations**: ALWAYS batch ALL memory store/retrieve in ONE message

### 🎯 CRITICAL: Claude Code Task Tool for Agent Execution

**Claude Code's Task tool is the PRIMARY way to spawn agents:**
```javascript
// ✅ CORRECT: Use Claude Code's Task tool for parallel agent execution
[Single Message]:
  Task("Research agent", "Analyze requirements and patterns...", "researcher")
  Task("Coder agent", "Implement core features...", "coder")
  Task("Tester agent", "Create comprehensive tests...", "tester")
  Task("Reviewer agent", "Review code quality...", "reviewer")
  Task("Architect agent", "Design system architecture...", "system-architect")
```

**MCP tools are ONLY for coordination setup:**
- `mcp__claude-flow__swarm_init` - Initialize coordination topology
- `mcp__claude-flow__agent_spawn` - Define agent types for coordination
- `mcp__claude-flow__task_orchestrate` - Orchestrate high-level workflows

### 📁 File Organization Rules

**NEVER save to root folder. Use these directories:**
- `/src` - Source code files
- `/tests` - Test files
- `/docs` - Documentation and markdown files
- `/config` - Configuration files
- `/scripts` - Utility scripts
- `/examples` - Example code

## Project Overview

This project uses SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) methodology with Claude-Flow orchestration for systematic Test-Driven Development.

## SPARC Commands

### Core Commands
- `npx claude-flow sparc modes` - List available modes
- `npx claude-flow sparc run <mode> "<task>"` - Execute specific mode
- `npx claude-flow sparc tdd "<feature>"` - Run complete TDD workflow
- `npx claude-flow sparc info <mode>` - Get mode details

### Batchtools Commands
- `npx claude-flow sparc batch <modes> "<task>"` - Parallel execution
- `npx claude-flow sparc pipeline "<task>"` - Full pipeline processing
- `npx claude-flow sparc concurrent <mode> "<tasks-file>"` - Multi-task processing

### Build Commands
- `npm run build` - Build project
- `npm run test` - Run tests
- `npm run lint` - Linting
- `npm run typecheck` - Type checking

## SPARC Workflow Phases

1. **Specification** - Requirements analysis (`sparc run spec-pseudocode`)
2. **Pseudocode** - Algorithm design (`sparc run spec-pseudocode`)
3. **Architecture** - System design (`sparc run architect`)
4. **Refinement** - TDD implementation (`sparc tdd`)
5. **Completion** - Integration (`sparc run integration`)

## Code Style & Best Practices

- **Modular Design**: Files under 500 lines
- **Environment Safety**: Never hardcode secrets
- **Test-First**: Write tests before implementation
- **Clean Architecture**: Separate concerns
- **Documentation**: Keep updated

## 🚀 Agent Autonomous Selection Framework

### 🤖 Claude's Orchestration Role
**Claude acts as orchestrator ONLY:**
- High-level task analysis and decomposition
- Initial agent spawning with autonomous selection criteria
- Progress monitoring and coordination
- Final integration and quality assurance

**Agents handle ALL implementation:**
- Technology stack decisions
- Detailed design and architecture
- Code implementation and testing
- Documentation and deployment

### 🎯 Intelligent Agent Selection System

**Auto-Selection Triggers:**
```javascript
// Claude spawns with selection criteria, not specific agents
Task("Smart Agent Selection", "Analyze task requirements. Auto-select appropriate agents based on:
- Technology stack keywords (Next.js → frontend-developer)
- Task type (API → backend-dev, Testing → tester)
- Project context (Trading system → quantitative-analyst)
- Complexity level (Simple → coder, Complex → system-architect)
Then execute the work autonomously.", "smart-agent")
```

### 🗺️ Agent Capability Matrix

#### Frontend Technologies
- **Next.js/React**: `frontend-developer`, `typescript-pro`
- **Mobile**: `mobile-dev`, `react-native-specialist`
- **UI/UX**: `trading-system-designer`, `ui-visual-validator`

#### Backend Technologies
- **Node.js/Express**: `backend-architect`, `typescript-pro`
- **Python/FastAPI**: `python-pro`, `korean-stock-api-debugger`
- **Database**: `database-admin`, `performance-monitor`

#### Trading & Finance
- **Algorithm Trading**: `quantitative-analyst`, `trading-engine-specialist`
- **Risk Management**: `risk-manager`, `performance-monitor`
- **Market Data**: `market-data-engineer`, `korean-stock-api-debugger`

#### DevOps & Infrastructure
- **CI/CD**: `cicd-engineer`, `debugger`
- **Performance**: `performance-monitor`, `database-admin`
- **Security**: `security-manager`, `code-analyzer`

#### Code Quality & Testing
- **Testing**: `tester`, `debugger`, `production-validator`
- **Code Review**: `reviewer`, `typescript-pro`, `python-pro`
- **Architecture**: `system-architect`, `backend-architect`

### 🎛️ Autonomous Decision Framework

**Level 1: Technology Detection**
- File extensions (.tsx → frontend-developer)
- Package.json dependencies (next → frontend-developer)
- Import statements (fastapi → python-pro)

**Level 2: Context Analysis**
- Project type (trading → quantitative-analyst)
- Task complexity (refactor → reviewer, new feature → coder)
- Performance requirements (optimization → performance-monitor)

**Level 3: Dynamic Coordination**
- Agent collaboration (frontend + backend coordination)
- Skill complementarity (typescript-pro + debugger)
- Workload balancing (multiple agents for large tasks)

## 🎯 Orchestration Hierarchy: Claude → Agents → Implementation

### 🎼 Claude's Orchestration Role (HIGH-LEVEL ONLY):
- **Task Analysis**: Break down user requests into contexts
- **Agent Coordination**: Spawn smart-agents with autonomous selection criteria
- **Progress Monitoring**: Track overall progress and integration
- **Quality Assurance**: Final review and user communication
- **Context Preservation**: Maintain project memory and continuity

### 🤖 Autonomous Agents Handle ALL DECISIONS:
- **Technology Selection**: Choose frameworks, libraries, tools
- **Architecture Design**: Design patterns, structures, interfaces
- **Implementation Strategy**: Coding approaches, testing methods
- **Performance Optimization**: Efficiency improvements, scaling
- **Integration Coordination**: Inter-agent communication and handoffs

### 🛠️ Agent Implementation Powers:
- File operations (Read, Write, Edit, MultiEdit, Glob, Grep)
- Code generation and programming
- Bash commands and system operations
- Package management and dependencies
- Testing and debugging
- Git operations and version control
- Documentation and API design

### 🔄 MCP Tools Support Coordination:
- Swarm initialization (topology setup)
- Agent type definitions (coordination patterns)
- Memory management and persistence
- Neural pattern learning
- Performance tracking and metrics
- GitHub integration and automation

**KEY**: Claude orchestrates → Agents decide → Tools execute

## 🚀 Quick Setup

```bash
# Add MCP servers (Claude Flow required, others optional)
claude mcp add claude-flow npx claude-flow@alpha mcp start
claude mcp add ruv-swarm npx ruv-swarm mcp start  # Optional: Enhanced coordination
claude mcp add flow-nexus npx flow-nexus@latest mcp start  # Optional: Cloud features
```

## MCP Tool Categories

### Coordination
`swarm_init`, `agent_spawn`, `task_orchestrate`

### Monitoring
`swarm_status`, `agent_list`, `agent_metrics`, `task_status`, `task_results`

### Memory & Neural
`memory_usage`, `neural_status`, `neural_train`, `neural_patterns`

### GitHub Integration
`github_swarm`, `repo_analyze`, `pr_enhance`, `issue_triage`, `code_review`

### System
`benchmark_run`, `features_detect`, `swarm_monitor`

### Flow-Nexus MCP Tools (Optional Advanced Features)
Flow-Nexus extends MCP capabilities with 70+ cloud-based orchestration tools:

**Key MCP Tool Categories:**
- **Swarm & Agents**: `swarm_init`, `swarm_scale`, `agent_spawn`, `task_orchestrate`
- **Sandboxes**: `sandbox_create`, `sandbox_execute`, `sandbox_upload` (cloud execution)
- **Templates**: `template_list`, `template_deploy` (pre-built project templates)
- **Neural AI**: `neural_train`, `neural_patterns`, `seraphina_chat` (AI assistant)
- **GitHub**: `github_repo_analyze`, `github_pr_manage` (repository management)
- **Real-time**: `execution_stream_subscribe`, `realtime_subscribe` (live monitoring)
- **Storage**: `storage_upload`, `storage_list` (cloud file management)

**Authentication Required:**
- Register: `mcp__flow-nexus__user_register` or `npx flow-nexus@latest register`
- Login: `mcp__flow-nexus__user_login` or `npx flow-nexus@latest login`
- Access 70+ specialized MCP tools for advanced orchestration

## 🚀 Agent Execution Flow with Claude Code

### The Correct Pattern:

1. **Optional**: Use MCP tools to set up coordination topology
2. **REQUIRED**: Use Claude Code's Task tool to spawn agents that do actual work
3. **REQUIRED**: Each agent runs hooks for coordination
4. **REQUIRED**: Batch all operations in single messages

### Example Autonomous Agent Selection:

```javascript
// ✅ NEW: Claude provides high-level context, agents self-select
[Single Message - Autonomous Agent Orchestration]:
  Task("Autonomous Full-Stack Coordinator", "
    CONTEXT: Build trading dashboard with Next.js frontend and FastAPI backend

    AUTO-SELECT AND EXECUTE:
    1. Detect Next.js → spawn frontend-developer + typescript-pro
    2. Detect FastAPI → spawn python-pro + backend-architect
    3. Detect trading → spawn quantitative-analyst + risk-manager
    4. Auto-coordinate between teams using hooks and memory
    5. Self-organize testing with appropriate specialists

    AUTONOMOUS DECISIONS:
    - Technology choices (state management, database, etc.)
    - Architecture patterns (microservices, monolith, etc.)
    - Testing strategies (unit, integration, e2e)
    - Deployment approach (Docker, serverless, etc.)

    COORDINATION PROTOCOL:
    - Use memory for cross-agent communication
    - Implement hooks for real-time updates
    - Self-healing if agents encounter blockers
    - Progressive enhancement based on project needs
  ", "smart-agent")

  // Minimal todos - agents create their own detailed plans
  TodoWrite { todos: [
    {content: "Autonomous agent selection and coordination", status: "in_progress"},
    {content: "Self-organized development execution", status: "pending"},
    {content: "Cross-agent integration and testing", status: "pending"},
    {content: "Autonomous quality assurance", status: "pending"}
  ]}
```

### 🔄 Agent Self-Organization Patterns:

```javascript
// Pattern 1: Technology-Based Auto-Selection
Task("Smart Tech Agent", "
  ANALYZE PROJECT:
  - Scan package.json, imports, file extensions
  - Detect: Next.js + TypeScript + Trading context

  AUTO-SPAWN APPROPRIATE AGENTS:
  - Frontend: frontend-developer (Next.js expert)
  - Backend: python-pro (if FastAPI detected) OR typescript-pro (if Node.js)
  - Trading: quantitative-analyst + trading-engine-specialist
  - Quality: typescript-pro + debugger

  COORDINATE AUTONOMOUSLY:
  - Establish communication protocols
  - Define interfaces and contracts
  - Implement progressive development
", "smart-agent")

// Pattern 2: Task-Complexity Auto-Routing
Task("Complexity-Aware Agent", "
  ASSESS TASK COMPLEXITY:
  - Simple UI changes → frontend-developer
  - Complex algorithm → quantitative-analyst + system-architect
  - Performance issues → performance-monitor + debugger
  - New features → full team coordination

  SELF-SCALE BASED ON NEEDS:
  - Start with minimal agents
  - Dynamically spawn specialists as needed
  - Coordinate handoffs automatically
", "smart-agent")
```

## 📋 Autonomous Agent Protocol

### 🎯 Agent Self-Management Cycle:

**1️⃣ AUTONOMOUS INITIALIZATION:**
```bash
# Agent analyzes context and self-configures
npx claude-flow@alpha hooks pre-task --description "[auto-detected-task]"
npx claude-flow@alpha hooks session-restore --session-id "swarm-[id]"
npx claude-flow@alpha hooks auto-analyze --context "[project-type]" --tech-stack "[detected-stack]"
```

**2️⃣ SMART DECISION MAKING:**
```bash
# Agent makes autonomous decisions
npx claude-flow@alpha hooks decision-log --choice "[tech/approach]" --reasoning "[why]"
npx claude-flow@alpha hooks coordinate --with-agents "[relevant-agents]" --protocol "[communication-method]"
npx claude-flow@alpha hooks post-edit --file "[file]" --memory-key "swarm/[agent]/[decision]"
```

**3️⃣ CONTINUOUS COORDINATION:**
```bash
# Agent coordinates with others automatically
npx claude-flow@alpha hooks notify --message "[progress-update]" --broadcast-to "[related-agents]"
npx claude-flow@alpha hooks conflict-resolve --issue "[technical-conflict]" --propose "[solution]"
npx claude-flow@alpha hooks quality-check --self-assess "[code-quality]" --request-review "[if-needed]"
```

**4️⃣ AUTONOMOUS COMPLETION:**
```bash
# Agent completes and hands off
npx claude-flow@alpha hooks post-task --task-id "[completed-task]" --deliverables "[what-created]"
npx claude-flow@alpha hooks handoff --to-agent "[next-agent]" --context "[integration-notes]"
npx claude-flow@alpha hooks session-end --export-metrics true --learn-patterns true
```

### 🤝 Cross-Agent Coordination Patterns:

**Frontend ↔ Backend Coordination:**
- API contract negotiations
- Type definition sharing
- Integration testing coordination

**Development ↔ Testing Coordination:**
- Test case generation from requirements
- Continuous testing during development
- Quality feedback loops

**Architecture ↔ Implementation Coordination:**
- Design pattern enforcement
- Code review for architectural compliance
- Performance monitoring integration

## 🎯 Concurrent Execution Examples

### ✅ CORRECT WORKFLOW: MCP Coordinates, Claude Code Executes

```javascript
// Step 1: MCP tools set up coordination (optional, for complex tasks)
[Single Message - Coordination Setup]:
  mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }
  mcp__claude-flow__agent_spawn { type: "researcher" }
  mcp__claude-flow__agent_spawn { type: "coder" }
  mcp__claude-flow__agent_spawn { type: "tester" }

// Step 2: Claude Code Task tool spawns ACTUAL agents that do the work
[Single Message - Parallel Agent Execution]:
  // Claude Code's Task tool spawns real agents concurrently
  Task("Research agent", "Analyze API requirements and best practices. Check memory for prior decisions.", "researcher")
  Task("Coder agent", "Implement REST endpoints with authentication. Coordinate via hooks.", "coder")
  Task("Database agent", "Design and implement database schema. Store decisions in memory.", "code-analyzer")
  Task("Tester agent", "Create comprehensive test suite with 90% coverage.", "tester")
  Task("Reviewer agent", "Review code quality and security. Document findings.", "reviewer")
  
  // Batch ALL todos in ONE call
  TodoWrite { todos: [
    {id: "1", content: "Research API patterns", status: "in_progress", priority: "high"},
    {id: "2", content: "Design database schema", status: "in_progress", priority: "high"},
    {id: "3", content: "Implement authentication", status: "pending", priority: "high"},
    {id: "4", content: "Build REST endpoints", status: "pending", priority: "high"},
    {id: "5", content: "Write unit tests", status: "pending", priority: "medium"},
    {id: "6", content: "Integration tests", status: "pending", priority: "medium"},
    {id: "7", content: "API documentation", status: "pending", priority: "low"},
    {id: "8", content: "Performance optimization", status: "pending", priority: "low"}
  ]}
  
  // Parallel file operations
  Bash "mkdir -p app/{src,tests,docs,config}"
  Write "app/package.json"
  Write "app/src/server.js"
  Write "app/tests/server.test.js"
  Write "app/docs/API.md"
```

### ❌ WRONG (Manual Agent Selection):
```javascript
// Old way - Claude makes all decisions
Message 1: mcp__claude-flow__swarm_init
Message 2: Task("Frontend Dev", "Build React component", "frontend-developer")
Message 3: Task("Backend Dev", "Create API endpoint", "backend-dev")
// Claude is micromanaging!
```

### ✅ CORRECT (Autonomous Agent Selection):
```javascript
// New way - Agents make decisions
[Single Message - Autonomous Orchestration]:
Task("Smart Development Team", "
  USER WANTS: Trading dashboard with Next.js and real-time data

  AUTONOMOUS EXECUTION:
  - Analyze: Next.js + trading + real-time requirements
  - Auto-select: frontend-developer, quantitative-analyst, market-data-engineer
  - Coordinate: Use hooks for API contracts, memory for shared state
  - Implement: Complete solution with testing and integration
  - Report: What was built and how it works
", "smart-agent")

TodoWrite { todos: ["Autonomous development execution", "Integration and testing", "Quality assurance"] }
```

## Performance Benefits

- **84.8% SWE-Bench solve rate**
- **32.3% token reduction**
- **2.8-4.4x speed improvement**
- **27+ neural models**

## 🎪 Autonomous Agent Hooks Integration

### 🔍 Pre-Operation Intelligence
- **Smart Agent Selection**: Auto-detect optimal agents by project context
- **Technology Stack Analysis**: Scan dependencies and choose specialists
- **Complexity Assessment**: Scale agent team based on task difficulty
- **Resource Optimization**: Prepare development environment automatically
- **Context Loading**: Restore previous decisions and patterns

### 🚀 Real-Time Coordination
- **Cross-Agent Communication**: Seamless information sharing
- **Conflict Resolution**: Automatic technical decision mediation
- **Progress Synchronization**: Real-time status updates across agents
- **Quality Assurance**: Continuous code review and improvement
- **Pattern Learning**: Adaptive behavior based on project success

### 📊 Post-Operation Enhancement
- **Auto-Formatting**: Code style consistency across all agents
- **Neural Pattern Training**: Learn from successful implementations
- **Memory Persistence**: Store decisions for future reference
- **Performance Analysis**: Track efficiency and optimize workflows
- **Knowledge Export**: Share learnings across sessions

### 🧠 Session Intelligence
- **Context Restoration**: Automatically resume from previous sessions
- **Decision History**: Track and learn from past choices
- **Workflow Optimization**: Improve processes based on outcomes
- **Agent Performance**: Monitor and enhance individual agent capabilities
- **Project Evolution**: Adapt to changing requirements autonomously

## Advanced Features (v2.0.0)

- 🚀 Automatic Topology Selection
- ⚡ Parallel Execution (2.8-4.4x speed)
- 🧠 Neural Training
- 📊 Bottleneck Analysis
- 🤖 Smart Auto-Spawning
- 🛡️ Self-Healing Workflows
- 💾 Cross-Session Memory
- 🔗 GitHub Integration

## Integration Tips

1. Start with basic swarm init
2. Scale agents gradually
3. Use memory for context
4. Monitor progress regularly
5. Train patterns from success
6. Enable hooks automation
7. Use GitHub tools first

## Support

- Documentation: https://github.com/ruvnet/claude-flow
- Issues: https://github.com/ruvnet/claude-flow/issues
- Flow-Nexus Platform: https://flow-nexus.ruv.io (registration required for cloud features)

---

Remember: **Claude orchestrates → Agents autonomously decide → Tools execute!**

## 🚀 Quick Start: Autonomous Development

### Simple Command for Any Task:
```javascript
// Just describe what you want - agents will figure out how!
Task("Autonomous Development Team", "
  USER REQUEST: [your description here]

  AUTONOMOUS AGENT INSTRUCTIONS:
  1. Analyze the request and project context
  2. Auto-select appropriate specialists based on technology stack
  3. Coordinate among yourselves using hooks and memory
  4. Make all technical decisions autonomously
  5. Implement, test, and integrate the solution
  6. Report back with what was accomplished

  EXAMPLE AUTO-SELECTIONS:
  - Next.js mentioned → frontend-developer + typescript-pro
  - Trading/Finance → quantitative-analyst + risk-manager
  - API/Backend → backend-architect + python-pro
  - Performance → performance-monitor + debugger
  - Testing → tester + production-validator
", "smart-agent")
```

### Example Usage:
```bash
# Claude just says:
"I need a trading dashboard with real-time data"

# Agents automatically:
# 1. Detect trading context → spawn quantitative-analyst, trading-engine-specialist
# 2. Detect dashboard need → spawn frontend-developer, ui-visual-validator
# 3. Detect real-time data → spawn market-data-engineer, performance-monitor
# 4. Coordinate architecture, implement, test, and deliver
```

# 🎯 Autonomous Agent Guidelines

## For Claude (Orchestrator):
- **High-level coordination only** - no detailed implementation decisions
- **Spawn smart-agents** with context, let them choose specialists
- **Monitor progress** and integrate final results
- **Maintain user communication** and project continuity

## For Autonomous Agents:
- **Make ALL technical decisions** independently
- **Choose optimal technologies** based on project context
- **Coordinate with peer agents** using hooks and memory
- **Implement complete solutions** with testing and documentation
- **Self-organize workflows** and handle complexity autonomously

## File Management Rules:
- **Never save to root folder** - use appropriate subdirectories
- **Agents decide file structure** based on technology and patterns
- **Prefer editing existing files** over creating new ones
- **Create files only when necessary** for the solution
- **Document decisions in memory** for other agents to reference

# important-instruction-reminders
Claude: Orchestrate at high level, let agents decide implementation.
Agents: Make all technical decisions autonomously, coordinate via hooks.
Files: Organize properly, prefer editing, avoid unnecessary creation.
