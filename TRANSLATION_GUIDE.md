# Translation Guide for Aquarium AI

Thank you for your interest in translating Aquarium AI to other languages! This guide will help you contribute translations to make this integration accessible to more users worldwide.

## Available Languages

Currently supported languages:
- **English (en)** - Default language
- **German (de)** - Deutsch (Deutsche Übersetzung)

### Preview: German Translation

The German translation provides a fully localized experience:

**Configuration Dialog:**
- "Aquarium AI Setup" → "Aquarium AI Einrichtung"
- "Temperature Sensor" → "Temperatursensor"
- "pH Sensor" → "pH-Sensor"
- "Update Frequency" → "Aktualisierungsfrequenz"

**Services:**
- "Run AI Analysis" → "KI-Analyse ausführen"

All descriptions, help text, and error messages are also translated to provide a seamless experience for German-speaking users.

## How to Add a New Language

### 1. Choose Your Language Code

Use the standard ISO 639-1 two-letter language codes:
- `de` - German (Deutsch)
- `es` - Spanish (Español)
- `fr` - French (Français)
- `it` - Italian (Italiano)
- `nl` - Dutch (Nederlands)
- `pl` - Polish (Polski)
- `pt` - Portuguese (Português)
- `ru` - Russian (Русский)
- `zh` - Chinese (中文)
- `ja` - Japanese (日本語)
- And many more...

For a complete list, see: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

### 2. Create Your Translation File

1. Navigate to `custom_components/aquarium_ai/translations/`
2. Copy the `template.json` file or `en.json` file
3. Rename it to `[language_code].json` (e.g., `es.json` for Spanish)

### 3. Translate the Content

Open your new language file and translate all the text values while keeping the structure intact:

#### Important Rules:

- **DO NOT** change the JSON structure or key names
- **DO NOT** translate the keys (left side of the colon)
- **ONLY** translate the values (right side of the colon, inside quotes)
- Keep technical terms like "AI", "pH", "Home Assistant" as they are
- Maintain formatting like line breaks (`\n`) if present
- Keep placeholders exactly as they are (e.g., `%s`, `{value}`)

#### Example:

**English (en.json):**
```json
{
  "config": {
    "step": {
      "user": {
        "title": "Aquarium AI Setup",
        "data": {
          "tank_name": "Aquarium Name"
        }
      }
    }
  }
}
```

**Spanish (es.json):**
```json
{
  "config": {
    "step": {
      "user": {
        "title": "Configuración de Aquarium AI",
        "data": {
          "tank_name": "Nombre del Acuario"
        }
      }
    }
  }
}
```

### 4. What to Translate

The translation file contains the following sections:

#### Configuration Flow Strings
- **title**: Dialog titles
- **description**: Dialog descriptions
- **data**: Field labels
- **data_description**: Field help text

#### Error Messages
- Error messages shown when configuration fails

#### Options Flow Strings
- Similar to configuration flow, but for modifying existing setups

#### Service Strings
- Service names and descriptions

### 5. Testing Your Translation

After creating your translation file:

1. Copy the file to your Home Assistant's `custom_components/aquarium_ai/translations/` directory
2. Change your Home Assistant user profile language to match your translation
3. Go to Settings → Devices & Services → Add Integration → Aquarium AI
4. Verify that all text appears correctly in your language

### 6. Submit Your Translation

Once you've completed and tested your translation:

1. Fork this repository on GitHub
2. Add your translation file to `custom_components/aquarium_ai/translations/`
3. Update this guide to list your language in the "Available Languages" section
4. Create a Pull Request with a clear title like "Add Spanish translation"
5. In the PR description, mention:
   - The language you translated
   - That you've tested the translation
   - Any special considerations for your language

## Translation Tips

### Special Terms

Some terms should remain consistent:

- **AI** - Usually kept as "AI" in most languages
- **pH** - Always "pH" (not "PH" or "ph")
- **Home Assistant** - Brand name, keep as is
- **Sensor** - Translate to your language's equivalent
- **Camera** - Translate to your language's equivalent

### Aquarium-Specific Terms

Common aquarium terms to be aware of:
- **Salinity** - Salt concentration in water
- **Dissolved Oxygen** - Amount of oxygen dissolved in water
- **ORP** - Oxidation-Reduction Potential (sometimes kept as ORP in translations)
- **Specific Gravity (SG)** - Density measurement for saltwater
- **ppt/psu** - Parts per thousand / Practical Salinity Unit

### Formal vs. Informal

Consider the tone appropriate for your language:
- Home Assistant typically uses a friendly, professional tone
- Most languages use formal "you" (e.g., "Sie" in German, "usted" in Spanish)
- But some communities prefer informal tone - use your best judgment

### Regional Variations

If your language has significant regional differences:
- Use the most widely understood variant
- Avoid region-specific slang or idioms
- Consider creating separate files for major variants (e.g., `pt-BR` for Brazilian Portuguese, `pt` for European Portuguese)

## Translation Checklist

Before submitting your translation, verify:

- [ ] All strings are translated (no English text remaining)
- [ ] JSON syntax is valid (use a JSON validator if needed)
- [ ] Technical terms are translated appropriately
- [ ] pH is written as "pH" (not "PH" or "ph")
- [ ] No keys or structure was changed
- [ ] Tested in Home Assistant with your language selected
- [ ] Configuration flow works correctly
- [ ] Options flow works correctly
- [ ] Error messages display properly
- [ ] Service descriptions are clear

## Need Help?

If you have questions about translating:

1. Check existing translations (like `de.json`) for reference
2. Open an issue on GitHub asking for clarification
3. Join the discussion in an existing translation Pull Request
4. Look at Home Assistant's translation guidelines: https://developers.home-assistant.io/docs/internationalization/

## Credits

Community translations by:
- **German (de)**: Initial translation by the Aquarium AI community

Thank you for helping make Aquarium AI accessible to users worldwide! 🌍🐠
