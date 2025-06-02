
import React, { useState } from 'react';
import Button from './Button';
import { DivinationSystem } from '../types';

interface QuestionInputProps {
  selectedSystem: DivinationSystem | null;
  onSubmitQuestion: (question: string) => void;
  onGoBack: () => void;
}

const QuestionInput: React.FC<QuestionInputProps> = ({ selectedSystem, onSubmitQuestion, onGoBack }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmitQuestion(question.trim());
  };

  return (
    <div className="space-y-6 p-6 bg-slate-800 bg-opacity-70 rounded-xl shadow-2xl backdrop-blur-md">
      <h2 className="text-3xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-500">
        Focus Your Intent
      </h2>
      <p className="text-center text-gray-300">
        You've chosen <span className="font-semibold text-purple-300">{selectedSystem}</span>.
        What question or area of life do you wish to explore?
      </p>
      <form onSubmit={handleSubmit} className="space-y-6">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="E.g., 'What should I focus on for my personal growth?' or leave blank for general guidance..."
          rows={4}
          className="w-full p-3 bg-slate-700 bg-opacity-50 border border-slate-600 rounded-lg text-gray-200 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
        />
        <div className="flex flex-col sm:flex-row gap-4">
          <Button type="button" onClick={onGoBack} variant="outline" fullWidth>
            Change System
          </Button>
          <Button type="submit" variant="primary" fullWidth>
            Seek Guidance
          </Button>
        </div>
      </form>
    </div>
  );
};

export default QuestionInput;
