
import { SymbolInfo, DivinationSystem } from './types';

export const TAROT_SYMBOLS: SymbolInfo[] = [
  { id: "tarot_hermit", name: "L'Hermite (The Hermit)", system: DivinationSystem.Tarot, imagePromptDetails: "A wise old figure holding a lantern, symbolizing introspection, wisdom, and guidance. Rendered in a modern, minimalist, 'ligne claire' (clear line) esoteric tarot card style with sharp symbolic depth. The symbol should be isolated on a transparent background." },
  { id: "tarot_fool", name: "Le Mat (The Fool)", system: DivinationSystem.Tarot, imagePromptDetails: "A joyful, androgynous figure stepping towards a cliff edge with a small bundle on a stick, symbolizing new beginnings, faith, and spontaneity. Modern, minimalist, 'ligne claire' (clear line) esoteric tarot card style. The symbol should be isolated on a transparent background." },
  { id: "tarot_magician", name: "Le Bateleur (The Magician)", system: DivinationSystem.Tarot, imagePromptDetails: "A figure standing before a table with symbolic objects (wand, cup, sword, pentacle), one hand pointing up, one down, symbolizing willpower, skill, and manifestation. Modern, minimalist, 'ligne claire' (clear line) esoteric tarot card style. The symbol should be isolated on a transparent background." },
  { id: "tarot_priestess", name: "La Papesse (The High Priestess)", system: DivinationSystem.Tarot, imagePromptDetails: "A seated female figure, often between two pillars, holding a scroll, symbolizing intuition, mystery, and hidden knowledge. Modern, minimalist, 'ligne claire' (clear line) esoteric tarot card style. The symbol should be isolated on a transparent background." },
];

export const YIJING_SYMBOLS: SymbolInfo[] = [
  { id: "yijing_1", name: "Hexagram 1: 乾 (Qian / The Creative)", system: DivinationSystem.Yijing, imagePromptDetails: "Six solid horizontal lines stacked vertically, representing pure yang energy, strength, and heaven. Abstract modern symbolic art in a 'ligne claire' (clear line) style, conveying power and clarity. The hexagram should be isolated on a transparent background." },
  { id: "yijing_2", name: "Hexagram 2: 坤 (Kun / The Receptive)", system: DivinationSystem.Yijing, imagePromptDetails: "Six broken horizontal lines (dashed lines) stacked vertically, representing pure yin energy, devotion, and earth. Abstract modern symbolic art in a 'ligne claire' (clear line) style, conveying yielding and nourishment. The hexagram should be isolated on a transparent background." },
  { id: "yijing_3", name: "Hexagram 3: 屯 (Zhun / Difficulty at the Beginning)", system: DivinationSystem.Yijing, imagePromptDetails: "Visual representation of a sprout pushing through obstacles, symbolizing initial challenges and potential for growth. Abstract modern symbolic art in a 'ligne claire' (clear line) style with a dynamic, emergent feel. Combination of earthy and vibrant greens. The symbol should be isolated on a transparent background." },
];

export const ASTROLOGY_SYMBOLS: SymbolInfo[] = [
  { id: "astro_mars", name: "Mars", system: DivinationSystem.Astrology, imagePromptDetails: "The astrological glyph for Mars (circle with an arrow pointing northeast), representing action, desire, and assertion. Cosmic modern symbolic art in a 'ligne claire' (clear line) style with fiery reds and oranges, dynamic energy. The glyph should be isolated on a transparent background." },
  { id: "astro_venus", name: "Venus", system: DivinationSystem.Astrology, imagePromptDetails: "The astrological glyph for Venus (circle above a cross), representing love, beauty, harmony, and attraction. Cosmic modern symbolic art in a 'ligne claire' (clear line) style with soft pinks, greens, and copper tones, graceful energy. The glyph should be isolated on a transparent background." },
  { id: "astro_moon", name: "The Moon", system: DivinationSystem.Astrology, imagePromptDetails: "The astrological glyph for the Moon (crescent shape), representing emotions, intuition, the subconscious, and nurturing. Cosmic modern symbolic art in a 'ligne claire' (clear line) style with silvers, blues, and pearlescent whites, mystical flowing energy. The glyph should be isolated on a transparent background." },
  { id: "astro_sun", name: "The Sun", system: DivinationSystem.Astrology, imagePromptDetails: "The astrological glyph for the Sun (circle with a dot in the center), representing vitality, self-expression, and core identity. Cosmic modern symbolic art in a 'ligne claire' (clear line) style with golds, yellows, and radiant light. The glyph should be isolated on a transparent background." },
];

export const GEMINI_TEXT_MODEL = "gemini-2.5-flash-preview-04-17";
export const GEMINI_IMAGE_MODEL = "imagen-3.0-generate-002";

export const APP_TITLE = "Oriacle";
