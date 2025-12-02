/**
 * Performance monitoring utilities
 */

// Web Vitals tracking
export const trackWebVitals = () => {
  if (typeof window === 'undefined') return

  // Core Web Vitals
  const observer = new PerformanceObserver((list) => {
    list.getEntries().forEach((entry) => {
      const value = (entry as any).value || entry.duration || 0
      console.log(`${entry.name}: ${value}`)
      
      // You can send these metrics to your analytics service
      // analytics.track(entry.name, { value })
    })
  })

  // Observe different performance metrics
  try {
    observer.observe({ entryTypes: ['measure', 'navigation', 'paint'] })
  } catch (e) {
    // Fallback for older browsers
    console.warn('Performance Observer not supported')
  }
}

// Bundle size monitoring
export const logBundleSize = () => {
  if (typeof window === 'undefined') return

  const scripts = Array.from(document.querySelectorAll('script[src]'))
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
  
  console.group('Bundle Analysis')
  console.log('JavaScript files:', scripts.length)
  console.log('CSS files:', styles.length)
  
  // Log resource timing if available
  if ('performance' in window && 'getEntriesByType' in performance) {
    const resources = performance.getEntriesByType('resource')
    const jsResources = resources.filter(r => r.name.includes('.js'))
    const cssResources = resources.filter(r => r.name.includes('.css'))
    
    console.log('JS Resources loaded:', jsResources.length)
    console.log('CSS Resources loaded:', cssResources.length)
    
    const totalJSSize = jsResources.reduce((acc, r) => acc + ((r as any).transferSize || 0), 0)
    const totalCSSSize = cssResources.reduce((acc, r) => acc + ((r as any).transferSize || 0), 0)
    
    console.log(`Total JS size: ${(totalJSSize / 1024).toFixed(2)} KB`)
    console.log(`Total CSS size: ${(totalCSSSize / 1024).toFixed(2)} KB`)
  }
  console.groupEnd()
}

// Memory usage monitoring
export const monitorMemoryUsage = () => {
  if (typeof window === 'undefined') return

  // @ts-ignore - memory API is not in all browsers
  if ('memory' in performance) {
    const memory = (performance as any).memory
    console.log('Memory Usage:', {
      used: `${(memory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
      total: `${(memory.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
      limit: `${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`
    })
  }
}

// Lazy loading utility for images
export const lazyLoadImage = (img: HTMLImageElement, src: string) => {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const target = entry.target as HTMLImageElement
        target.src = src
        target.classList.remove('lazy')
        observer.unobserve(target)
      }
    })
  })

  observer.observe(img)
}

// Debounce utility for performance
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

// Throttle utility for performance
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

// Initialize performance monitoring
export const initPerformanceMonitoring = () => {
  if (process.env.NODE_ENV === 'development') {
    trackWebVitals()
    
    // Log bundle info after page load
    window.addEventListener('load', () => {
      setTimeout(() => {
        logBundleSize()
        monitorMemoryUsage()
      }, 1000)
    })
  }
}