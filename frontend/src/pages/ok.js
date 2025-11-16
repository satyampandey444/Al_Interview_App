import React, { useState } from 'react';

const initialAspects = [
  { id: 1, name: 'Readability', upvotes: 0, downvotes: 0 },
  { id: 2, name: 'Performance', upvotes: 0, downvotes: 0 },
  { id: 3, name: 'Security', upvotes: 0, downvotes: 0 },
  { id: 4, name: 'Documentation', upvotes: 0, downvotes: 0 },
  { id: 5, name: 'Testing', upvotes: 0, downvotes: 0 },
];

const FeedbackSystem = () => {
  const [aspects, setAspects] = useState(initialAspects);

  const handleVote = (id, type) => {
    const newAspects = aspects.map(aspect => {
      if (aspect.id === id) {
        return {
          ...aspect,
          [type]: aspect[type] + 1,
        };
      }
      return aspect;
    });

    setAspects(newAspects);
  };


  return (
    <div className="my-0 mx-auto text-center w-max-1200">
      <div className="flex wrap justify-content-center mt-30 gap-30">
        
        {aspects.map(aspect => (
          <div key={aspect.id} className="pa-10 w-300 card">
            <h2>{aspect.name}</h2> 
            
            <div className="flex my-30 mx-0 justify-content-around">
              <button 
                className="py-10 px-15 success" 
                data-testid={`upvote-btn-${aspect.id}`}
                onClick={() => handleVote(aspect.id, 'upvotes')}
              >
                👍 Upvote
              </button>
              <button 
                className="py-10 px-15 danger" 
                data-testid={`downvote-btn-${aspect.id}`}
                onClick={() => handleVote(aspect.id, 'downvotes')}
              >
                👎 Downvote
              </button>
            </div>
            
            <p className="my-10 mx-0" data-testid={`upvote-count-${aspect.id}`}>
              Upvotes: 
              <strong className="count-animation">{aspect.upvotes}</strong>
            </p>
            
            <p className="my-10 mx-0" data-testid={`downvote-count-${aspect.id}`}>
              Downvotes: 
              <strong className="count-animation">{aspect.downvotes}</strong>
            </p>
          </div>
        ))}

      </div>
    </div>
  );
};

export default FeedbackSystem;