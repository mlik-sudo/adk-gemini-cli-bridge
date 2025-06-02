
import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { SymbolInfo, DivinationSystem, Interpretation } from '../types';
import { GEMINI_TEXT_MODEL, GEMINI_IMAGE_MODEL } from '../constants';

let ai: GoogleGenAI | null = null;

function getAiClient(): GoogleGenAI {
  if (ai) {
    return ai;
  }

  let apiKeyFromEnv: string | undefined;
  // Safely access process.env.API_KEY
  if (typeof process !== 'undefined' && process.env && typeof process.env.API_KEY === 'string') {
    apiKeyFromEnv = process.env.API_KEY;
  }

  if (!apiKeyFromEnv) {
    const errorMsg = "API Key is not available. Ensure 'process.env.API_KEY' is correctly set and accessible in the execution environment.";
    console.error(errorMsg);
    throw new Error(errorMsg);
  }

  ai = new GoogleGenAI({ apiKey: apiKeyFromEnv });
  return ai;
}

export const generateSymbolImage = async (symbol: SymbolInfo): Promise<string> => {
  try {
    const client = getAiClient(); // Initializes client and checks API key on first call
    const prompt = `Illustrate the ${symbol.system} symbol: "${symbol.name}". ${symbol.imagePromptDetails}. The image should be suitable for a divination app, with a modern, clean, and symbolic aesthetic. Focus on a central iconic representation. Ensure the final image is visually appealing and clear.`;
    
    const response = await client.models.generateImages({
      model: GEMINI_IMAGE_MODEL,
      prompt: prompt,
      config: { numberOfImages: 1, outputMimeType: 'image/png' },
    });

    if (response.generatedImages && response.generatedImages.length > 0 && response.generatedImages[0].image?.imageBytes) {
      const base64ImageBytes = response.generatedImages[0].image.imageBytes;
      return `data:image/png;base64,${base64ImageBytes}`;
    } else {
      console.error("No image generated or empty response structure from API.", response);
      throw new Error("No image generated or API response was malformed.");
    }
  } catch (e) {
    console.error("Error generating symbol image:", e);
    if (e instanceof Error) {
        // Re-throw the error to be caught by the caller, preserving its message.
        // If it's the API key error from getAiClient, it's already specific.
        throw new Error(`Image generation failed: ${e.message}`);
    }
    throw new Error("An unknown error occurred during image generation.");
  }
};

export const generateInterpretation = async (symbol: SymbolInfo, userQuestion: string): Promise<Interpretation> => {
  try {
    const client = getAiClient(); // Initializes client and checks API key on first call
    const systemInstruction = `You are an AI expert in Jungian psychology, ${symbol.system}, and symbolic interpretation, acting as a wise and empathetic guide for an interactive divination app called "Oriacle". Your interpretations should be insightful, personalized, and encourage introspection.`;
    
    const promptContent = `
    The user has selected the divination system: ${symbol.system}.
    The drawn symbol is: "${symbol.name}".
    The user's personal question/focus is: "${userQuestion || "General guidance related to the symbol."}".

    Please generate a personalized interpretation. The response MUST be a valid JSON object with the following structure and content guidelines:
    {
      "symbolName": "${symbol.name}",
      "jungianFrame": "Concisely explain the symbol within a Jungian archetypal framework. Focus on its core archetypal significance and how it relates to the psyche. (approx. 50-70 words)",
      "psychologicalExploration": "Explore the psychological implications of this symbol, particularly in relation to the user's stated question or focus. Offer insights into their current inner state, potential challenges, or opportunities for growth. (approx. 70-100 words)",
      "integrationExercise": "Suggest a practical, introspective exercise related to the symbol's meaning and the psychological exploration. This should be a concrete action the user can take for self-reflection or integration. (approx. 30-50 words, phrased as a gentle suggestion)"
    }

    Maintain a tone that is academic yet accessible, rigorous but metaphorical, empathetic, and insightful.
    Ensure the \`symbolName\` in the JSON output exactly matches the drawn symbol: "${symbol.name}".
    If the user's question is very generic or missing, provide a general interpretation for the symbol that still feels personal and useful.
    `;

    const response: GenerateContentResponse = await client.models.generateContent({
      model: GEMINI_TEXT_MODEL,
      contents: promptContent,
      config: {
        systemInstruction: systemInstruction,
        responseMimeType: "application/json",
        temperature: 0.7,
      },
    });

    const rawText = response.text;
    if (typeof rawText !== 'string') {
      console.error("API response for interpretation did not contain a valid text field:", response);
      throw new Error("Invalid or missing text response from API for interpretation.");
    }
    let jsonStr = rawText.trim();
    
    const fenceRegex = /^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$/s;
    const match = jsonStr.match(fenceRegex);
    if (match && match[1]) {
      jsonStr = match[1].trim();
    }
    
    try {
      const parsedData = JSON.parse(jsonStr);
      if (parsedData.symbolName && parsedData.jungianFrame && parsedData.psychologicalExploration && parsedData.integrationExercise) {
        return parsedData as Interpretation;
      } else {
        console.error("Parsed JSON is missing required fields:", parsedData);
        throw new Error("Interpretation structure from API is invalid.");
      }
    } catch (parseError) {
      console.error("Failed to parse JSON response:", parseError, "Original string for context:", response.text);
      throw new Error(`Failed to parse interpretation from API response. Raw text: ${response.text.substring(0,100)}...`);
    }

  } catch (e) {
    console.error("Error generating interpretation:", e);
    if (e instanceof Error) {
        throw new Error(`Interpretation generation failed: ${e.message}`);
    }
    throw new Error("An unknown error occurred during interpretation generation.");
  }
};
