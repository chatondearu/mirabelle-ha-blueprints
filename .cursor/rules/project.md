# Project Rules

## Project Structure
- Keep blueprints organized in appropriate subdirectories (automations, scripts, scenes, dashboards)
- Maintain documentation in the `docs` directory
- Use clear and descriptive filenames
- Follow the established directory structure:
  ```
  mirabelle-ha-blueprints/
  ├── blueprints/
  │   ├── automations/
  │   └── scripts/
  ├── docs/
  └── README.md
  ```

## Documentation
- Write all documentation in English
- Include installation instructions with direct links
- Provide clear examples for each blueprint
- Document all configuration parameters
- Include troubleshooting sections
- Add integration examples with other blueprints

## Blueprint Development
- Use clear and descriptive names
- Include comprehensive input parameters
- Provide sensible defaults
- Add helpful descriptions for each parameter
- Use proper selectors for input types
- Make triggers optional when possible
- Support multiple trigger types

## Code Style
- Use consistent YAML formatting
- Add comments for complex logic
- Use descriptive variable names
- Follow Home Assistant best practices
- Keep blueprints modular and reusable

## Version Control
- Use semantic versioning
- Write clear commit messages
- Follow conventional commit format:
  - feat: new feature
  - fix: bug fix
  - docs: documentation
  - style: formatting
  - refactor: code refactoring

## Testing
- Test blueprints before committing
- Verify all parameters work as expected
- Check integration with other blueprints
- Test edge cases and error conditions

## User Experience
- Provide clear installation instructions
- Include usage examples
- Document prerequisites
- Add troubleshooting guides
- Make configuration intuitive

## Security
- Don't include sensitive information
- Use proper input validation
- Follow Home Assistant security guidelines
- Document any security considerations

## Maintenance
- Keep documentation up to date
- Update blueprints for Home Assistant changes
- Monitor for deprecation warnings
- Maintain backward compatibility when possible

## Contribution Guidelines
- Fork the repository
- Create a new branch
- Follow the established structure
- Update documentation
- Submit a pull request

## Best Practices
- Keep blueprints simple and focused
- Use descriptive names
- Provide clear documentation
- Include examples
- Make configuration flexible
- Support multiple use cases
- Consider edge cases
- Test thoroughly
- Document changes
- Keep code clean and maintainable
- Keep all texts in english (no other language)

## Commit & Push after modification

After any change to configuration files (e.g. blueprints, scripts, settings, documentation, README, etc.), you must:

1. Commit the changes locally with a clear and explicit message.
2. Push the changes to the remote repository to ensure project traceability and synchronization.