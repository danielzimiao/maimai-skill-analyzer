import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadZone } from './components/UploadZone'
import { analyzeChart, type AnalysisResult } from './api'

type AppState = 'idle' | 'analyzing' | 'results'

function App() {
  const [appState, setAppState] = useState<AppState>('idle')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [results, setResults] = useState<AnalysisResult | null>(null)
  const [activeBrowseTag, setActiveBrowseTag] = useState<string | null>(null)

  // Suppress unused variable warnings during development
  void uploadedFile
  void results
  void activeBrowseTag
  void setActiveBrowseTag

  const handleFileSelect = async (file: File) => {
    setUploadedFile(file)
    setAppState('analyzing')
    try {
      const result = await analyzeChart(file)
      setResults(result)
      setAppState('results')
    } catch (err) {
      console.error('Analysis failed:', err)
      setAppState('idle')
    }
  }

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
            <UploadZone onFileSelect={handleFileSelect} />
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
            className="w-1/2 flex items-center justify-center border-r border-gray-800 p-8"
          >
            <UploadZone onFileSelect={handleFileSelect} />
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
