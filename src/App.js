import React from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import './App.css'; // App-specific styles

function App() {
  return (
    <div>
      <Header />
      <div style={{ display: 'flex' }}>
        <Sidebar />
        <main style={{ flex: 1, padding: '1rem' }}>
          <h1>Welcome to My App</h1>
          <p>This is the main content area.</p>
        </main>
      </div>
      <Footer />
    </div>
  );
}

export default App;