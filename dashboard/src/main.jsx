import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

console.log('Starting React application...');

// Add global error handler
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
});

const rootElement = document.getElementById('root');
if (!rootElement) {
  console.error('Root element not found!');
} else {
  console.log('Root element found, mounting React...');
  try {
    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>,
    );
    console.log('React application mounted successfully');
  } catch (error) {
    console.error('Error mounting React application:', error);
    rootElement.innerHTML = `
      <div style="color: white; padding: 20px; font-family: sans-serif; background: #070a12; min-height: 100vh;">
        <h1>Application Error</h1>
        <p>Failed to load the application. Please check the console for details.</p>
        <p>Error: ${error.message}</p>
        <p>Stack: ${error.stack}</p>
      </div>
    `;
  }
}
