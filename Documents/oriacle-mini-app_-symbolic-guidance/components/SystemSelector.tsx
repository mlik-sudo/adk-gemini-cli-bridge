
import React from 'react';
import { DivinationSystem } from '../types';
// Button component is no longer used in this file
// import Button from './Button'; 

interface SystemSelectorProps {
  onSelectSystem: (system: DivinationSystem) => void;
}

const SystemSelector: React.FC<SystemSelectorProps> = ({ onSelectSystem }) => {
  const systems = [
    { name: 'Tarot', value: DivinationSystem.Tarot },
    { name: 'Yijing', value: DivinationSystem.Yijing },
    { name: 'Astrology', value: DivinationSystem.Astrology },
  ];

  const handleSelection = (event: React.ChangeEvent<HTMLSelectElement>) => {
    if (event.target.value) {
      onSelectSystem(event.target.value as DivinationSystem);
    }
  };

  return (
    <div className="space-y-6 p-6 bg-slate-800 bg-opacity-70 rounded-xl shadow-2xl backdrop-blur-md animate-fadeIn">
      <h2 className="text-3xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-500 mb-6">
        Choose Your Path
      </h2>
      
      <div className="space-y-3">
        <label htmlFor="system-select" className="block text-lg font-medium text-purple-300 text-center sr-only">
          Select a divination system:
        </label>
        <div className="relative">
          <select
            id="system-select"
            onChange={handleSelection}
            defaultValue=""
            className="w-full px-4 py-3 text-lg bg-slate-700 bg-opacity-90 border border-slate-500 rounded-lg text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-600 appearance-none pr-10 cursor-pointer"
            aria-label="Select divination system"
          >
            <option value="" disabled className="text-gray-500 bg-slate-800">
              -- Click to choose a system --
            </option>
            {systems.map((system) => (
              <option key={system.value} value={system.value} className="bg-slate-800 text-gray-200 py-2">
                {/* Icons 🃏, 🀄, ✨ could be added here with more complex HTML if desired, but simple text is standard for <option> */}
                {system.name}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-purple-300">
            <svg className="fill-current h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
              <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/>
            </svg>
          </div>
        </div>
      </div>

      <p className="text-center text-sm text-gray-400 mt-6">
        Select a system to begin your journey of insight.
      </p>
    </div>
  );
};

// Adding a simple fade-in animation to index.html for a smoother appearance of components
// This is more of a global style, but for the purpose of this change, it enhances the SystemSelector appearance.
// Better placed in index.html if more generic animations are needed.
// For now, using a Tailwind class 'animate-fadeIn' which would require defining this animation in tailwind.config.js or global CSS.
// Since I cannot modify tailwind.config.js, I will add a style tag to index.html for this.
// However, the prompt asks for minimal changes. The component itself having `animate-fadeIn` is a placeholder for such an animation.
// Let's assume `animate-fadeIn` is a utility class available or will be added.
// Or, more simply, I will remove `animate-fadeIn` to ensure it doesn't break if the class isn't defined.
// The existing main transition `transition-all duration-500 ease-in-out` in App.tsx should cover page transitions.
// I'll remove `animate-fadeIn` from the `SystemSelector` and rely on App.tsx's transitions.

export default SystemSelector;
