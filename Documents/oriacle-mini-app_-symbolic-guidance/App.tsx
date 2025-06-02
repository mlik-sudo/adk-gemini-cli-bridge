
import React, { useState, useEffect, useCallback } from 'react';
import { DivinationSystem, SymbolInfo, Interpretation, AppStep } from './types';
import { TAROT_SYMBOLS, YIJING_SYMBOLS, ASTROLOGY_SYMBOLS, APP_TITLE } from './constants';
import { generateSymbolImage, generateInterpretation } from './services/geminiService';

import SystemSelector from './components/SystemSelector';
import QuestionInput from './components/QuestionInput';
import SymbolCard from './components/SymbolCard';
import InterpretationDisplay from './components/InterpretationDisplay';
import LoadingSpinner from './components/LoadingSpinner';
import Button from './components/Button'; // Button is still used for "New Guidance" and in QuestionInput

const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<AppStep>(AppStep.SELECT_SYSTEM);
  const [selectedSystem, setSelectedSystem] = useState<DivinationSystem | null>(null);
  const [userQuestion, setUserQuestion] = useState<string>("");
  const [drawnSymbol, setDrawnSymbol] = useState<SymbolInfo | null>(null);
  const [symbolImageUrl, setSymbolImageUrl] = useState<string | null>(null);
  const [interpretation, setInterpretation] = useState<Interpretation | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isCardRevealed, setIsCardRevealed] = useState<boolean>(false);

  const resetState = useCallback(() => {
    setCurrentStep(AppStep.SELECT_SYSTEM);
    setSelectedSystem(null);
    setUserQuestion("");
    setDrawnSymbol(null);
    setSymbolImageUrl(null);
    setInterpretation(null);
    setIsLoading(false);
    setError(null);
    setIsCardRevealed(false);
  }, []);

  const handleSystemSelect = (system: DivinationSystem) => {
    setSelectedSystem(system);
    setCurrentStep(AppStep.ENTER_QUESTION);
    setError(null);
  };

  const handleQuestionSubmit = (question: string) => {
    setUserQuestion(question);
    setCurrentStep(AppStep.SHOW_RESULT);
    setIsLoading(true);
    setError(null);
    // Reset previous results for a fresh display
    setDrawnSymbol(null);
    setSymbolImageUrl(null);
    setInterpretation(null);
    setIsCardRevealed(false);
  };

  const fetchGuidance = useCallback(async () => {
    if (!selectedSystem || !drawnSymbol) return;

    try {
      // API key check is handled by geminiService now.
      // If process.env.API_KEY is not set, geminiService functions will throw.
      
      const imageUrl = await generateSymbolImage(drawnSymbol);
      setSymbolImageUrl(imageUrl);
      
      // Reveal card after image URL is fetched
      // Add a small delay for the image to potentially load if it's fast
      setTimeout(() => setIsCardRevealed(true), 300); 

      const interp = await generateInterpretation(drawnSymbol, userQuestion);
      setInterpretation(interp);

    } catch (e) {
      console.error("Guidance generation failed:", e);
      if (e instanceof Error) {
        setError(`Error: ${e.message}. Please check your API key and network, then try again.`);
      } else {
        setError("An unknown error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [selectedSystem, drawnSymbol, userQuestion]);


  useEffect(() => {
    // This effect should run when:
    // 1. We are in the SHOW_RESULT step.
    // 2. A system has been selected.
    // 3. No symbol has been drawn for the current session yet (drawnSymbol is null).
    // 4. We are in the loading state (isLoading is true), indicating a new session has started.
    if (currentStep === AppStep.SHOW_RESULT && selectedSystem && !drawnSymbol && isLoading) {
      let symbols: SymbolInfo[] = [];
      switch (selectedSystem) {
        case DivinationSystem.Tarot: symbols = TAROT_SYMBOLS; break;
        case DivinationSystem.Yijing: symbols = YIJING_SYMBOLS; break;
        case DivinationSystem.Astrology: symbols = ASTROLOGY_SYMBOLS; break;
        default: 
          setError("Invalid system selected."); 
          setIsLoading(false); // Stop loading if system is invalid
          return;
      }
      if (symbols.length === 0) {
        setError("No symbols available for this system."); 
        setIsLoading(false); // Stop loading if no symbols
        return;
      }
      const randomIndex = Math.floor(Math.random() * symbols.length);
      setDrawnSymbol(symbols[randomIndex]);
      // isLoading remains true, fetchGuidance effect will pick it up.
    }
  }, [currentStep, selectedSystem, drawnSymbol, isLoading]);


  useEffect(() => {
    // This effect triggers the API calls once drawnSymbol is set and we are still in loading state.
    if (drawnSymbol && isLoading) { 
        fetchGuidance();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drawnSymbol, isLoading]); // fetchGuidance is memoized

  const renderStepContent = () => {
    switch (currentStep) {
      case AppStep.SELECT_SYSTEM:
        return <SystemSelector onSelectSystem={handleSystemSelect} />;
      case AppStep.ENTER_QUESTION:
        return <QuestionInput selectedSystem={selectedSystem} onSubmitQuestion={handleQuestionSubmit} onGoBack={resetState} />;
      case AppStep.SHOW_RESULT:
        return (
          <div className="flex flex-col items-center space-y-8 w-full">
            {isLoading && !drawnSymbol && <LoadingSpinner message="Preparing your guidance..." size={12} />}
            
            {drawnSymbol && (
              <SymbolCard 
                imageUrl={symbolImageUrl} 
                altText={drawnSymbol.name} 
                isRevealed={isCardRevealed} 
              />
            )}

            {/* Show interpreting message only if image has been fetched or symbol is drawn and we're waiting for text */}
            {isLoading && drawnSymbol && !interpretation && <LoadingSpinner message="Interpreting the symbols..." size={10} />}
            
            {!isLoading && interpretation && <InterpretationDisplay interpretation={interpretation} />}
            
            {/* Show "New Guidance" button if not loading AND (either a symbol was drawn OR an error occurred) */}
            {!isLoading && (drawnSymbol || error) && (
                <Button onClick={resetState} variant="secondary" size="lg" className="mt-8">
                New Guidance
                </Button>
            )}
          </div>
        );
      default:
        return <p>Unknown step.</p>;
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center p-4 antialiased">
      <header className="text-center mb-8">
        <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-500 to-orange-400">
          {APP_TITLE}
        </h1>
        <p className="text-lg text-purple-200 mt-2">Symbolic Insights for Your Journey</p>
      </header>

      <main className="w-full max-w-md mx-auto transition-all duration-500 ease-in-out">
        {error && (
          <div className="bg-red-500 bg-opacity-80 text-white p-4 rounded-lg mb-6 shadow-lg text-center">
            <p className="font-semibold">Oops! Something went wrong.</p>
            <p className="text-sm">{error}</p>
          </div>
        )}
        {renderStepContent()}
      </main>

      <footer className="text-center mt-12 text-xs text-slate-500">
        <p>&copy; {new Date().getFullYear()} {APP_TITLE}. AI-powered guidance.</p>
        <p>Interpretations are for introspection and entertainment purposes only.</p>
      </footer>
    </div>
  );
};

export default App;
