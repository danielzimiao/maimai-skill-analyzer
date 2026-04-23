import { useRef, useState } from 'react'

interface UploadZoneProps {
  onFileSelect: (file: File) => void
}

const VALID_EXTENSIONS = ['.txt', '.zip', '.axlv']

function isValidFile(file: File): boolean {
  return VALID_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(ext))
}

export function UploadZone({ onFileSelect }: UploadZoneProps) {
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFile(file: File) {
    if (!isValidFile(file)) {
      setError(
        'Unable to analyze — only maidata.txt or .zip/.axlv chart files are supported',
      )
      return
    }
    setError(null)
    onFileSelect(file)
  }

  function handleDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  function handleClick() {
    inputRef.current?.click()
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    // Reset so the same file can be re-selected
    e.target.value = ''
  }

  return (
    <div
      className="border-2 border-dashed border-gray-600 hover:border-blue-400 rounded-xl p-12 text-center cursor-pointer transition-colors"
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <div className="text-gray-400 text-lg mb-2">Drop your chart file here</div>
      <div className="text-gray-500 text-sm">or click to browse</div>
      <div className="text-gray-500 text-xs mt-2">.txt, .zip, .axlv</div>
      {error && <div className="text-red-400 text-sm mt-4">{error}</div>}
      <input
        ref={inputRef}
        type="file"
        accept=".txt,.zip,.axlv"
        className="hidden"
        onChange={handleInputChange}
      />
    </div>
  )
}
