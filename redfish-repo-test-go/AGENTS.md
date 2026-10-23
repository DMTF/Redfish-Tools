# AGENTS.md

## Setup commands
- Install deps: `go mod download`
- Run tests: `go test -cover ./...`
- Run tests checking for race conditions: `go test -race ./...`
- Run linter: `golangci-lint run ./...`

## Code style
- Golang: follow Go 1.21+ conventions
- Use clear, descriptive variable names
- Keep functions small and focused
- Add comments for complex logic
- Follow Go naming conventions
- All test files should have a _test suffix and be implemented in a _test package
- Each package should have a minimum code coverage of 80% from unit tests