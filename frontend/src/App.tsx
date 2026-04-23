import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

type AppState = 'idle' | 'analyzing' | 'results'

interface AnalysisResult {
  difficulty: number | null
  tags: string[]
  similar_songs: Array<{
    name: string
    difficulty: number | null
    release_date: string | null
    bg_image_url: string | null
  }>
}

function App() {
  const [appState, setAppState] = useState<AppState>('idle')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [results, setResults] = useState<AnalysisResult | null>(null)
  const [activeBrowseTag, setActiveBrowseTag] = useState<string | null>(null)

  // Suppress unused variable warnings during development
  void uploadedFile
  void results
  void activeBrowseTag

  function handleSimulate() {
    if (appState === 'idle') setAppState('analyzing')
    else if (appState === 'analyzing') setAppState('results')
    else setAppState('idle')
  }

  const simulateLabel =
    appState === 'idle'
      ? 'Simulate analyzing'
      : appState === 'analyzing'
      ? 'Simulate results'
      : 'Reset'

  const UploadZonePlaceholder = () => (
    <div className="w-full max-w-md border-2 border-dashed border-gray-700 rounded-2xl p-12 flex flex-col items-center gap-4 text-gray-500">
      <svg
        className="w-12 h-12 text-gray-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
        />
      </svg>
      <p className="text-sm text-center">
        Drop your maimai chart file here
        <br />
        <span className="text-xs text-gray-600">or click to browse</span>
      </p>
      <button
        onClick={handleSimulate}
        className="mt-2 px-4 py-2 rounded-lg bg-purple-700 hover:bg-purple-600 text-white text-sm font-medium transition-colors"
      >
        {simulateLabel}
      </button>
    </div>
  )

  return (
    <AnimatePresence mode="wait">
      {appState === 'idle' ? (
        <motion.div
          key="idle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="min-h-screen bg-gray-950 flex items-center justify-center"
        >
          <div className="w-full max-w-md flex flex-col items-center gap-6">
            <h1 className="text-3xl font-bold text-white tracking-tight">
              maimai Skill Gap Analyzer
            </h1>
            <p className="text-gray-400 text-sm text-center">
              Upload a chart to analyze difficulty and find similar songs
            </p>
            <UploadZonePlaceholder />
          </div>
        </motion.div>
      ) : (
        <motion.div
          key="split"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="min-h-screen bg-gray-950 flex"
        >
          {/* Left panel — upload zone */}
          <motion.div
            initial={{ x: -40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="w-1/2 flex items-center justify-center border-r border-gray-800"
          >
            <UploadZonePlaceholder />
          </motion.div>

          {/* Right panel — analyzing or results */}
          <motion.div
            initial={{ x: 40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="w-1/2 flex items-center justify-center p-8"
          >
            {appState === 'analyzing' ? (
              <div className="flex flex-col items-center gap-4 text-gray-300">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
                  className="w-10 h-10 border-2 border-purple-500 border-t-transparent rounded-full"
                />
                <p className="text-lg font-medium text-gray-200">Analyzing...</p>
                <p className="text-sm text-gray-500">
                  Extracting difficulty and tags from your chart
                </p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4 text-gray-300">
                <p className="text-2xl font-semibold text-white">Results here</p>
                <p className="text-sm text-gray-500">
                  Difficulty, tags, and similar songs will appear here
                </p>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default App
