import { Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Analyzer from './pages/Analyzer'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/analyze" element={<Analyzer />} />
    </Routes>
  )
}
