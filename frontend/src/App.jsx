import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera } from '@react-three/drei';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ParticleSwarmScene } from './components/ParticleSwarmScene';
import './index.css';

gsap.registerPlugin(ScrollTrigger);

function App() {
  const [model, setModel] = useState('1'); // '1' | '2' | 'compare'
  const [text, setText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  const [activeSection, setActiveSection] = useState(0);
  const [isMobile, setIsMobile] = useState(false);
  const mainRef = useRef();

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Setup GSAP ScrollTriggers to track the active section
  useEffect(() => {
    const sections = gsap.utils.toArray('section');
    sections.forEach((sec, i) => {
      ScrollTrigger.create({
        trigger: sec,
        start: 'top center',
        end: 'bottom center',
        onToggle: self => {
          if (self.isActive) setActiveSection(i);
        }
      });
    });

    return () => {
      ScrollTrigger.getAll().forEach(t => t.kill());
    };
  }, []);

  const wordCount = text.trim().split(/\s+/).filter(w => w.length > 0).length;

  const handleAnalyze = async (overrideModel = null) => {
    // If the event object is passed, ignore it
    const isEvent = overrideModel && typeof overrideModel === 'object' && overrideModel.nativeEvent;
    const currentModel = (overrideModel && !isEvent) ? overrideModel : model;

    if (!text.trim()) {
      if (!currentModel || isEvent) {
        setError("Please enter a meaningful news article.");
      }
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    // Scroll automatically to the analysis/result section for a cinematic effect
    const analysisSection = document.getElementById('section-analysis');
    if (analysisSection) {
      analysisSection.scrollIntoView({ behavior: 'smooth' });
    }

    const apiUrl = import.meta.env.VITE_API_URL !== undefined ? import.meta.env.VITE_API_URL : 'http://localhost:8888';

    try {
      if (currentModel === 'compare') {
        const [resBase, resPso] = await Promise.all([
          fetch(`${apiUrl}/api/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, model_choice: '1' })
          }),
          fetch(`${apiUrl}/api/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, model_choice: '2' })
          })
        ]);

        const dataBase = await resBase.json();
        const dataPso = await resPso.json();

        if (!resBase.ok) throw new Error(dataBase.detail || "An unexpected server error occurred.");
        if (!resPso.ok) throw new Error(dataPso.detail || "An unexpected server error occurred.");

        // Artificial delay for cinematic processing effect
        await new Promise(r => setTimeout(r, 2000));

        setResult({
          baseline: dataBase,
          pso: dataPso,
          disagreement: dataBase.prediction !== dataPso.prediction
        });

      } else {
        const response = await fetch(`${apiUrl}/api/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, model_choice: currentModel })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "An unexpected server error occurred.");
        
        await new Promise(r => setTimeout(r, 2000));
        setResult(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleModelSelect = (selectedModel) => {
    setModel(selectedModel);
    if (text.trim() && !isAnalyzing) {
      handleAnalyze(selectedModel);
    }
  };

  const handleClear = () => {
    setText('');
    setResult(null);
    setError(null);
  };

  return (
    <>
      <div id="canvas-container" aria-hidden="true">
        <Canvas dpr={isMobile ? [1, 1] : [1, 1.5]} performance={{ min: 0.5 }}>
          <PerspectiveCamera makeDefault position={[0, 0, 20]} fov={45} />
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={2} />
          <ParticleSwarmScene 
            activeSection={activeSection} 
            isAnalyzing={isAnalyzing} 
            result={result} 
            model={model}
            isMobile={isMobile} 
          />
        </Canvas>
      </div>

      <nav className="fixed-nav">
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.5rem', letterSpacing: '-0.05em' }}>FND</div>
        <div className="mono-text" style={{ textAlign: 'right' }}>
          01 HERO<br/>
          02 PSO<br/>
          03 DETECTOR
        </div>
      </nav>

      <main ref={mainRef}>
        
        {/* 01 HERO */}
        <section id="section-hero">
          <div style={{ maxWidth: '1200px' }}>
            <h1 className="huge-text">FAKE<br/>NEWS<br/>DETECTION</h1>
            <div style={{ marginTop: '2rem', display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
              <div>
                <p className="mono-text">ARCHITECTURE</p>
                <p style={{ fontSize: '1.25rem', fontWeight: 500 }}>Neural Classification</p>
              </div>
              <div>
                <p className="mono-text">OPTIMIZATION</p>
                <p style={{ fontSize: '1.25rem', fontWeight: 500 }}>Particle Swarm Search</p>
              </div>
            </div>
            <div style={{ marginTop: '10vh' }} className="mono-text">SCROLL TO EXPLORE ↓</div>
          </div>
        </section>

        {/* 03 HOW IT WORKS (Inference) */}
        <section id="section-works">
          <div style={{ maxWidth: '800px', marginLeft: 'auto' }}>
            <h2 className="large-text" style={{ marginBottom: '4rem' }}>THE<br/>PIPELINE</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <PipelineStage num="01" title="RAW ARTICLE" desc="The input text is ingested in its raw format." />
              <PipelineStage num="02" title="CLEANING" desc="Stopwords, punctuation, and noise are stripped." />
              <PipelineStage num="03" title="TF-IDF" desc="Words are vectorized based on corpus frequency." />
              <PipelineStage num="04" title="NEURAL NETWORK" desc="An MLP identifies learned linguistic patterns." />
              <PipelineStage num="05" title="CLASSIFICATION" desc="A probability score determines REAL or FAKE." />
            </div>
          </div>
        </section>

        {/* 04 PSO */}
        <section id="section-pso" style={{ justifyContent: 'center' }}>
          <div style={{ maxWidth: '1000px' }}>
            <h2 className="large-text">PARTICLE<br/>SWARM<br/>OPTIMIZATION</h2>
            <p style={{ fontSize: '1.5rem', maxWidth: '600px', margin: '2rem 0' }}>
              To maximize accuracy, we deployed a virtual swarm. Hundreds of candidate configurations searched the hyperparameter space to discover the global optimum.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem', marginTop: '4rem' }}>
              <div style={{ borderTop: '1px solid var(--text-dim)', paddingTop: '1rem' }}>
                <p className="mono-text">HIDDEN DIMENSION</p>
                <p className="large-text" style={{ color: 'var(--accent)' }}>89</p>
              </div>
              <div style={{ borderTop: '1px solid var(--text-dim)', paddingTop: '1rem' }}>
                <p className="mono-text">LEARNING RATE</p>
                <p className="large-text" style={{ color: 'var(--accent)' }}>0.002</p>
              </div>
              <div style={{ borderTop: '1px solid var(--text-dim)', paddingTop: '1rem' }}>
                <p className="mono-text">DROPOUT</p>
                <p className="large-text" style={{ color: 'var(--accent)' }}>0.371</p>
              </div>
            </div>
          </div>
        </section>

        {/* 05 DETECTOR */}
        <section id="section-detector">
          <div style={{ maxWidth: '1000px', width: '100%' }}>
            <h2 className="large-text" style={{ marginBottom: '2rem' }}>ANALYZE<br/>A PIECE<br/>OF NEWS</h2>
            
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
              <button 
                className={`mono-text ${model === '1' ? 'active-tab' : ''}`}
                style={{ padding: '0.5rem 1rem', border: `1px solid ${model === '1' ? 'var(--text-main)' : 'var(--text-dim)'}`, color: model === '1' ? 'var(--bg-main)' : 'var(--text-main)', background: model === '1' ? 'var(--text-main)' : 'transparent', borderRadius: '100px', cursor: 'pointer' }}
                onClick={() => handleModelSelect('1')}
              >
                BASELINE
              </button>
              <button 
                className={`mono-text ${model === '2' ? 'active-tab' : ''}`}
                style={{ padding: '0.5rem 1rem', border: `1px solid ${model === '2' ? 'var(--text-main)' : 'var(--text-dim)'}`, color: model === '2' ? 'var(--bg-main)' : 'var(--text-main)', background: model === '2' ? 'var(--text-main)' : 'transparent', borderRadius: '100px', cursor: 'pointer' }}
                onClick={() => handleModelSelect('2')}
              >
                PSO OPTIMIZED
              </button>
              <button 
                className={`mono-text ${model === 'compare' ? 'active-tab' : ''}`}
                style={{ padding: '0.5rem 1rem', border: `1px solid ${model === 'compare' ? 'var(--text-main)' : 'var(--text-dim)'}`, color: model === 'compare' ? 'var(--bg-main)' : 'var(--text-main)', background: model === 'compare' ? 'var(--text-main)' : 'transparent', borderRadius: '100px', cursor: 'pointer' }}
                onClick={() => handleModelSelect('compare')}
              >
                COMPARE
              </button>
            </div>

            <textarea
              className="minimal-input"
              placeholder="Paste a news article here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={isAnalyzing}
            />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
              <div className="mono-text">
                {wordCount} WORDS / {text.length} CHARACTERS
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button onClick={handleClear} disabled={isAnalyzing || !text} style={{ color: 'var(--text-secondary)', cursor: 'pointer', background: 'none', border: 'none', textTransform: 'uppercase', letterSpacing: '0.1em', fontSize: '0.8rem' }}>CLEAR</button>
                <button className="minimal-btn" onClick={() => handleAnalyze()} disabled={isAnalyzing || !text.trim()}>
                  {isAnalyzing ? 'ANALYZING...' : 'ANALYZE →'}
                </button>
              </div>
            </div>

            {error && (
              <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid var(--fake)', color: 'var(--fake)', fontFamily: 'monospace' }}>
                ERROR: {error}
              </div>
            )}
          </div>
        </section>

        {/* 06 & 07 ANALYSIS & RESULTS */}
        <section id="section-analysis" style={{ minHeight: (result || isAnalyzing) ? '100vh' : '0vh', opacity: (result || isAnalyzing) ? 1 : 0, transition: 'opacity 0.5s', overflow: 'hidden' }}>
          {isAnalyzing && (
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
              <h2 className="large-text">PROCESSING</h2>
              <div className="mono-text" style={{ marginTop: '2rem' }}>Extracting features & evaluating patterns...</div>
            </div>
          )}

          {result && !isAnalyzing && (
            <div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
              <h2 className="large-text" style={{ marginBottom: '2rem' }}>RESULT</h2>
              
              {model === 'compare' ? (
                <div>
                  <div style={{ marginBottom: '4rem', padding: '2rem', border: `2px solid ${result.disagreement ? 'var(--warn)' : 'var(--accent)'}` }}>
                    <h3 className="medium-text" style={{ color: result.disagreement ? 'var(--warn)' : 'var(--text-main)' }}>
                      {result.disagreement ? 'MODEL DISAGREEMENT' : 'MODEL AGREEMENT'}
                    </h3>
                    <p style={{ marginTop: '1rem', fontSize: '1.25rem' }}>
                      {result.disagreement 
                        ? "The two model configurations produced different classifications. This indicates uncertainty between model configurations on this specific text."
                        : "Both model configurations produced the exact same classification."}
                    </p>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '4rem' }}>
                    <CompareColumn title="BASELINE MLP" data={result.baseline} />
                    <CompareColumn title="PSO OPTIMIZED MLP" data={result.pso} />
                  </div>
                </div>
              ) : (
                <div style={{ borderTop: '2px solid var(--text-dim)', paddingTop: '2rem' }}>
                  <h3 className="huge-text" style={{ color: result.prediction === 'REAL' ? 'var(--real)' : 'var(--fake)' }}>
                    {result.prediction}
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem', marginTop: '4rem' }}>
                    <div>
                      <p className="mono-text">MODEL CONFIDENCE</p>
                      <p className="medium-text">{(result.confidence * 100).toFixed(2)}%</p>
                      <ConfidenceLabel conf={result.confidence} />
                    </div>
                    <div>
                      <p className="mono-text">EVALUATED BY</p>
                      <p className="medium-text">{result.model}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* 08 RESEARCH & FOOTER */}
        <section id="section-research" style={{ minHeight: '80vh', justifyContent: 'flex-end', paddingBottom: '10vh' }}>
          <div style={{ maxWidth: '800px' }}>
            <h2 className="medium-text" style={{ marginBottom: '2rem' }}>RESEARCH LIMITATIONS</h2>
            <p style={{ fontSize: '1.25rem', color: 'var(--text-secondary)' }}>
              This system is a machine-learning classifier trained on the project dataset. Model confidence represents the classifier's confidence in its learned pattern classification; it does not represent factual certainty or independent fact-checking.
            </p>
            <p style={{ fontSize: '1.25rem', color: 'var(--text-secondary)', marginTop: '1rem' }}>
              The Particle Swarm Optimization (PSO) searched the hyperparameter space to maximize validation accuracy. While the optimized model found the `89 / 0.002 / 0.371` configuration, it may perform similarly to the baseline on certain out-of-distribution texts.
            </p>
          </div>
        </section>

      </main>
    </>
  );
}

function PipelineStage({ num, title, desc }) {
  return (
    <div style={{ display: 'flex', gap: '2rem', borderBottom: '1px solid var(--text-dim)', paddingBottom: '1rem' }}>
      <div className="mono-text">{num}</div>
      <div>
        <h3 style={{ fontSize: '2rem' }}>{title}</h3>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>{desc}</p>
      </div>
    </div>
  );
}

function CompareColumn({ title, data }) {
  return (
    <div>
      <p className="mono-text" style={{ borderBottom: '1px solid var(--text-dim)', paddingBottom: '1rem', marginBottom: '2rem' }}>
        {title}
      </p>
      <h3 className="medium-text" style={{ color: data.prediction === 'REAL' ? 'var(--real)' : 'var(--fake)', marginBottom: '2rem' }}>
        {data.prediction}
      </h3>
      <p className="mono-text">CONFIDENCE</p>
      <p className="medium-text" style={{ marginBottom: '0.5rem' }}>{(data.confidence * 100).toFixed(2)}%</p>
      <ConfidenceLabel conf={data.confidence} />
    </div>
  );
}

function ConfidenceLabel({ conf }) {
  let label = "LOW MODEL CONFIDENCE";
  let color = "var(--text-secondary)";
  if (conf >= 0.8) {
    label = "HIGH MODEL CONFIDENCE";
    color = "var(--text-main)";
  } else if (conf >= 0.6) {
    label = "MODERATE MODEL CONFIDENCE";
    color = "var(--warn)";
  }
  return <p className="mono-text" style={{ color, marginTop: '0.5rem' }}>{label}</p>;
}

export default App;
