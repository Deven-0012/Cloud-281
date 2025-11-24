import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Shell from './components/layout/Shell';
import HomePage from './pages/HomePage';
import Analytics from './pages/Analytics';
import Alerts from './pages/Alerts';
import Devices from './pages/Devices';
import Cars from './pages/Cars';
import AlertDetails from './pages/AlertDetails'
import LoginPage from './pages/LoginPage';
import RegisterPage  from './pages/RegisterPage';

export default function App() {
return (


<React.Suspense fallback={<div className="p-6">Loading…</div>}>
<Routes>
<Route path="/" element={<HomePage />} />
<Route path='/login' element= {<LoginPage/>} />
<Route path='/register' element= {<RegisterPage/>} />
<Route path="/alerts" element={< Alerts/>} />
<Route path="/alerts/:id" element={<AlertDetails />} />
<Route path="/cars" element={<Cars />} />
<Route path="/analytics" element={<Analytics />} />
<Route path="/devices" element={<Devices />} />
</Routes>
</React.Suspense>


);
}