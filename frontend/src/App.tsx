import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Result from './pages/Result'
import History from './pages/History'

export default function App() {
  return (
    <div className="min-h-screen" style={{ background: '#0D0D0D' }}>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/result/:id" element={<Result />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </div>
  )
}
