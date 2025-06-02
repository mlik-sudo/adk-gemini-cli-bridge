
export enum DivinationSystem {
  Tarot = "Tarot",
  Yijing = "Yijing",
  Astrology = "Astrology",
}

export interface SymbolInfo {
  id: string;
  name: string;
  system: DivinationSystem;
  imagePromptDetails: string;
}

export interface Interpretation {
  symbolName: string;
  jungianFrame: string;
  psychologicalExploration: string;
  integrationExercise: string;
}

export enum AppStep {
  SELECT_SYSTEM,
  ENTER_QUESTION,
  SHOW_RESULT,
}

// Describes the structure of grounding chunks if used with Google Search
export interface GroundingChunkWeb {
  uri: string;
  title: string;
}
export interface GroundingChunk {
  web?: GroundingChunkWeb;
  // other types of chunks can be added if needed
}
export interface GroundingMetadata {
  groundingChunks?: GroundingChunk[];
  // other grounding metadata fields
}
