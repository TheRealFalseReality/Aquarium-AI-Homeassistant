# Contributing to Aquarium AI

Thank you for your interest in contributing to Aquarium AI! This document provides guidelines and information for contributors.

## Ways to Contribute

There are many ways you can contribute to this project:

### 🌍 Translations

Help make Aquarium AI accessible to users worldwide by translating it into your language!

- **Difficulty**: Easy
- **Time**: 30-60 minutes
- **Guide**: See [TRANSLATION_GUIDE.md](TRANSLATION_GUIDE.md) for detailed instructions

Current translations:
- English (en) - Default
- German (de)

We'd love to have translations for Spanish, French, Italian, Dutch, Polish, Portuguese, Russian, Chinese, Japanese, and many more!

### 🐛 Bug Reports

Found a bug? Help us fix it by providing detailed information:

1. Search existing issues to avoid duplicates
2. Create a new issue with:
   - Clear title describing the problem
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Your Home Assistant version
   - Integration version
   - Relevant logs (enable debug logging if needed)
   - Screenshots if applicable

### 💡 Feature Requests

Have an idea for a new feature or improvement?

1. Check existing issues for similar requests
2. Open a new issue describing:
   - The feature you'd like to see
   - Why it would be useful
   - How you envision it working
   - Any examples from other integrations

### 💻 Code Contributions

Want to contribute code? Great! Here's how:

#### Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Development Setup

This is a Home Assistant custom integration. To test your changes:

1. Copy the `custom_components/aquarium_ai` folder to your Home Assistant's `config/custom_components/` directory
2. Restart Home Assistant
3. Test your changes thoroughly

#### Code Guidelines

- Follow Home Assistant's coding standards
- Keep changes focused and minimal
- Test your changes with real sensors/cameras if possible
- Update documentation if you change user-facing features
- Add comments for complex logic

#### Before Submitting

- [ ] Test your changes in a real Home Assistant environment
- [ ] Ensure no syntax errors or warnings
- [ ] Update documentation if needed
- [ ] Add yourself to credits if making significant contributions

#### Submitting a Pull Request

1. Push your changes to your fork
2. Create a Pull Request from your fork to the main repository
3. Provide a clear description of:
   - What the PR does
   - Why the change is needed
   - How to test it
   - Any breaking changes
4. Link to related issues if applicable

## Development Guidelines

### Project Structure

```
custom_components/aquarium_ai/
├── __init__.py           # Integration setup and core logic
├── config_flow.py        # Configuration UI flow
├── const.py              # Constants and defaults
├── manifest.json         # Integration metadata
├── sensor.py             # Sensor entities
├── services.yaml         # Service definitions
├── strings.json          # Default English strings
└── translations/         # Language-specific translations
    ├── en.json          # English
    ├── de.json          # German
    └── template.json    # Translation template
```

### Key Components

- **Config Flow**: UI for setting up the integration
- **Sensors**: AI analysis sensors for each parameter
- **AI Analysis**: Core logic that calls Home Assistant's AI task service
- **Notifications**: Formatted notifications with analysis results

### Testing

Since this integration relies on AI services and sensors:

1. Test with real aquarium sensors if possible
2. Test with different AI providers (Google AI, OpenAI, etc.)
3. Test different aquarium types (Freshwater, Marine, Reef)
4. Test with and without camera integration
5. Test all notification formats (Full, Condensed, Minimal)
6. Test manual vs automatic analysis modes

### Debug Logging

To enable debug logging in Home Assistant, add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.aquarium_ai: debug
```

## Translation Contributions

Translations are especially welcome! They're easy to contribute and have a big impact.

1. See [TRANSLATION_GUIDE.md](TRANSLATION_GUIDE.md) for full instructions
2. Use `translations/template.json` as your starting point
3. Test your translation in Home Assistant
4. Submit a PR with your new language file

## Documentation

When adding features, please update:

- README.md - User-facing features and setup instructions
- TRANSLATION_GUIDE.md - If adding translatable strings
- This file - If adding new contribution types

## Community Guidelines

- Be respectful and constructive
- Help others when you can
- Share your aquarium setups and results!
- Have fun - this is a passion project! 🐠

## Questions?

- Open an issue for questions about contributing
- Check existing issues and PRs for similar discussions
- Review closed issues for historical context

## Recognition

Contributors are recognized in:
- This file
- TRANSLATION_GUIDE.md (for translators)
- Release notes (for significant contributions)

Thank you for helping make Aquarium AI better! 🌟
