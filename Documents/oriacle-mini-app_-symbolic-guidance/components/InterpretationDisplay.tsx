
import React from 'react';
import { Interpretation } from '../types';

interface InterpretationDisplayProps {
  interpretation: Interpretation | null;
}

const InterpretationSection: React.FC<{ title: string; content: string; icon: string }> = ({ title, content, icon }) => (
  <div className="bg-slate-800 bg-opacity-60 p-4 rounded-lg shadow-lg backdrop-blur-sm">
    <h3 className="text-xl font-semibold text-purple-300 mb-2 flex items-center">
      <span className="mr-2 text-2xl" aria-hidden="true">{icon}</span>
      {title}
    </h3>
    <p className="text-gray-300 leading-relaxed">{content}</p>
  </div>
);

const InterpretationDisplay: React.FC<InterpretationDisplayProps> = ({ interpretation }) => {
  if (!interpretation) {
    return null;
  }

  return (
    <div className="space-y-6 mt-8 w-full">
      <h2 className="text-3xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-500">
        Wisdom of <span className="italic">{interpretation.symbolName}</span>
      </h2>
      
      <InterpretationSection 
        title="Jungian Framework" 
        content={interpretation.jungianFrame}
        icon="🧠"
      />
      <InterpretationSection 
        title="Psychological Exploration" 
        content={interpretation.psychologicalExploration}
        icon="🧭"
      />
      <InterpretationSection 
        title="Introspective Exercise" 
        content={interpretation.integrationExercise}
        icon="🧘"
      />
    </div>
  );
};

export default InterpretationDisplay;