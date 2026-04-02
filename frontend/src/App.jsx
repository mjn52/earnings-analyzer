import { Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import Analyzer from './pages/Analyzer'
import Terms from './pages/Terms'
import Privacy from './pages/Privacy'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/analyze" element={<Analyzer />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />
    </Routes>
  )
}
