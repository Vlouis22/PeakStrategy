import { useState, useEffect } from "react";

const ResearchLoadingAnimation = ({ ticker }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [showPleaseWait, setShowPleaseWait] = useState(false);

  const steps = [
    { text: `Gathering information about ${ticker}`, duration: 4500 },
    { text: "Analyzing financial statements", duration: 5000 },
    { text: "Processing market data", duration: 4500 },
    { text: "Reviewing valuation metrics", duration: 5000 },
    { text: "Compiling analyst insights", duration: 4500 },
    { text: "Finalizing research report", duration: 5000 },
  ];

  useEffect(() => {
    const thirtySecondTimer = setTimeout(() => {
      setShowPleaseWait(true);
      setProgress(100);
    }, 30000);

    return () => clearTimeout(thirtySecondTimer);
  }, []);

  useEffect(() => {
    if (showPleaseWait) return;

    const stepDuration = steps[currentStep].duration;
    const startTime = Date.now();

    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const stepProgress = Math.min((elapsed / stepDuration) * 100, 100);
      setProgress(stepProgress);
    }, 30);

    const stepTimeout = setTimeout(() => {
      setCurrentStep((prev) => (prev + 1) % steps.length);
      setProgress(0);
    }, stepDuration);

    return () => {
      clearInterval(progressInterval);
      clearTimeout(stepTimeout);
    };
  }, [currentStep, showPleaseWait]);

  return (
    <div className="flex items-center justify-center min-h-[550px] py-8">
      <div className="w-full max-w-3xl px-8">
        <div className="space-y-10">
          {/* Ticker Display */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center gap-3 px-6 py-3 bg-neutral-50 border border-neutral-200 rounded-full">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-status-pulse"></div>
              <span className="text-sm font-medium text-neutral-600 tracking-wide">
                ANALYZING
              </span>
            </div>
          </div>

          {/* Animated Visualization */}
          <div className="relative h-56 flex items-center justify-center">
            {/* Outer rings */}
            <div className="absolute inset-0 flex items-center justify-center">
              {[0, 1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="absolute rounded-full border"
                  style={{
                    width: `${140 + i * 70}px`,
                    height: `${140 + i * 70}px`,
                    borderColor: `rgba(163, 163, 163, ${0.15 - i * 0.03})`,
                    animation: `pulse-ring ${3.5 + i * 0.8}s cubic-bezier(0.4, 0, 0.6, 1) infinite`,
                    animationDelay: `${i * 0.4}s`,
                  }}
                />
              ))}
            </div>

            {/* Orbiting dots */}
            {[0, 1, 2].map((i) => (
              <div
                key={`orbit-${i}`}
                className="absolute"
                style={{
                  width: `${200 + i * 60}px`,
                  height: `${200 + i * 60}px`,
                  animation: `orbit ${8 + i * 2}s linear infinite`,
                  animationDelay: `${-i * 1.5}s`,
                }}
              >
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-neutral-400 rounded-full"></div>
              </div>
            ))}

            {/* Center element */}
            <div className="relative z-10">
              <div className="w-28 h-28 rounded-full bg-gradient-to-br from-neutral-50 to-neutral-100 border border-neutral-200 shadow-2xl flex items-center justify-center backdrop-blur-sm">
                <svg
                  className="w-14 h-14 text-neutral-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Status Text */}
          <div className="relative h-20 overflow-hidden">
            {showPleaseWait ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="text-3xl font-light text-neutral-800 tracking-tight mb-3">
                  Please wait...
                </div>
                <div className="flex items-center gap-2">
                  {[...Array(6)].map((_, i) => (
                    <div
                      key={i}
                      className="w-8 h-1 rounded-full bg-neutral-800"
                    />
                  ))}
                </div>
              </div>
            ) : (
              steps.map((step, index) => (
                <div
                  key={index}
                  className={`absolute inset-0 flex flex-col items-center justify-center transition-all duration-1000 ease-in-out ${
                    index === currentStep
                      ? "opacity-100 translate-y-0 scale-100"
                      : index < currentStep
                      ? "opacity-0 -translate-y-12 scale-95"
                      : "opacity-0 translate-y-12 scale-95"
                  }`}
                >
                  <div className="text-3xl font-light text-neutral-800 tracking-tight mb-3">
                    {step.text}
                  </div>
                  <div className="flex items-center gap-2">
                    {steps.map((_, i) => (
                      <div
                        key={i}
                        className={`h-1 rounded-full transition-all duration-500 ${
                          i === currentStep
                            ? "w-12 bg-neutral-800"
                            : i < currentStep
                            ? "w-8 bg-neutral-400"
                            : "w-6 bg-neutral-200"
                        }`}
                      />
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Progress Bar */}
          <div className="space-y-3">
            <div className="relative h-2 bg-neutral-100 rounded-full overflow-hidden shadow-inner">
              <div
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-neutral-600 via-neutral-700 to-neutral-800 rounded-full transition-all duration-100 ease-linear shadow-sm"
                style={{ width: `${progress}%` }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer"></div>
              </div>
            </div>
            
            <div className="text-center text-sm text-neutral-400 tracking-wide">
              Estimated time: 20-30 seconds
            </div>
          </div>
        </div>

        <style>{`
          @keyframes pulse-ring {
            0%, 100% {
              opacity: 0.4;
              transform: scale(0.92);
            }
            50% {
              opacity: 0.08;
              transform: scale(1.08);
            }
          }
          
          @keyframes orbit {
            0% {
              transform: rotate(0deg);
            }
            100% {
              transform: rotate(360deg);
            }
          }

          @keyframes shimmer {
            0% {
              transform: translateX(-100%);
            }
            100% {
              transform: translateX(100%);
            }
          }

          @keyframes status-pulse {
            0%, 100% {
              opacity: 0.2;
            }
            50% {
              opacity: 1;
            }
          }

          .animate-shimmer {
            animation: shimmer 2s infinite;
          }

          .animate-status-pulse {
            animation: status-pulse 1.5s ease-in-out infinite;
          }
        `}</style>
      </div>
    </div>
  );
};

export default ResearchLoadingAnimation;