// ABSOLUTE MINIMAL - NO REACT, JUST VANILLA JS

console.log('=== MAIN-SIMPLE.TSX LOADED ===')

const root = document.getElementById('root')

if (root) {
  console.log('Root found, injecting HTML...')
  
  root.innerHTML = `
    <div style="
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: system-ui, -apple-system, sans-serif;
      color: white;
    ">
      <div style="text-align: center; max-width: 600px; padding: 40px;">
        <h1 style="font-size: 72px; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
          ✅ IT WORKS!
        </h1>
        <p style="font-size: 24px; margin-bottom: 30px;">
          Frontend is loading successfully!
        </p>
        <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
          <p style="font-size: 18px; line-height: 1.8;">
            ✓ Vite dev server: RUNNING<br/>
            ✓ JavaScript: EXECUTING<br/>
            ✓ DOM: ACCESSIBLE<br/>
            ✓ Styles: WORKING
          </p>
        </div>
        <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px;">
          <p style="font-size: 14px; margin-bottom: 10px;">
            <strong>Backend:</strong> http://localhost:8000<br/>
            <strong>Frontend:</strong> http://localhost:3000<br/>
            <strong>Login:</strong> admin / admin123
          </p>
        </div>
        <p style="font-size: 12px; margin-top: 20px; opacity: 0.7;">
          This is a minimal test without React. If you see this, the problem is with React dependencies.
        </p>
      </div>
    </div>
  `
  
  console.log('HTML injected successfully!')
} else {
  console.error('ERROR: Root element not found!')
  document.body.innerHTML = '<h1 style="color: red; padding: 50px;">ERROR: Root element not found!</h1>'
}

