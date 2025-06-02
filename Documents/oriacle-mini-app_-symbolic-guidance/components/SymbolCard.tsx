
import React, { useState, useEffect } from 'react';

interface SymbolCardProps {
  imageUrl: string | null;
  altText: string;
  isRevealed: boolean;
}

const SymbolCard: React.FC<SymbolCardProps> = ({ imageUrl, altText, isRevealed }) => {
  const [showImage, setShowImage] = useState(false);

  useEffect(() => {
    if (isRevealed && imageUrl) {
      // Delay slightly to allow placeholder to render if needed, then animate in
      const timer = setTimeout(() => setShowImage(true), 100);
      return () => clearTimeout(timer);
    } else if (!isRevealed) {
      setShowImage(false);
    }
  }, [isRevealed, imageUrl]);

  return (
    <div className="w-64 h-96 md:w-80 md:h-[448px] bg-slate-700 bg-opacity-50 rounded-xl shadow-2xl overflow-hidden perspective p-2 group">
      <div 
        className={`relative w-full h-full preserve-3d transition-transform duration-[600ms] ease ${showImage ? '' : 'rotate-y-180'}`}
      >
        {/* Front of card (placeholder shown while image loads or before reveal) */}
        <div className="absolute w-full h-full backface-hidden bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-16 h-16 text-purple-200 opacity-50">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L1.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.25 12L15.404 9.813a4.5 4.5 0 00-3.09-3.09L9.75 5.25l2.846-.813a4.5 4.5 0 003.09-3.09L18.25 0l.813 2.846a4.5 4.5 0 003.09 3.09L25 7.5l-2.846.813a4.5 4.5 0 00-3.09 3.09L18.25 12zM9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L1.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
        </div>
        {/* Back of card (image) */}
        <div className="absolute w-full h-full backface-hidden rotate-y-180 bg-slate-800 rounded-lg overflow-hidden">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={altText}
              className={`w-full h-full object-cover transition-all duration-700 ease-in-out ${showImage ? 'opacity-100 scale-100' : 'opacity-0 scale-90'}`}
              onError={(e) => (e.currentTarget.src = 'https://picsum.photos/320/448?grayscale')} // Fallback image
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              Loading symbol...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SymbolCard;