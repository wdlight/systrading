// Simple chart debugging script
// Run this in browser console at http://localhost:9000/test-chart

console.log('=== Chart Debug Script ===');

// Check if we're in browser
console.log('1. Environment check:');
console.log('- Window available:', typeof window !== 'undefined');
console.log('- Document available:', typeof document !== 'undefined');

// Check chart containers
console.log('2. Chart containers:');
const chartContainers = document.querySelectorAll('.bg-\\[\\#0a0a0b\\]');
console.log('- Chart containers found:', chartContainers.length);

chartContainers.forEach((container, index) => {
  console.log(`Container ${index}:`, {
    text: container.textContent?.substring(0, 100),
    classes: container.className,
    children: container.children.length
  });
});

// Check for error messages
console.log('3. Error messages:');
const errorMsgs = document.querySelectorAll('*');
Array.from(errorMsgs).forEach(el => {
  if (el.textContent && el.textContent.includes('차트 로딩 실패')) {
    console.log('- Error found:', el.textContent);
  }
});

// Try to import lightweight-charts directly in browser
console.log('4. Testing dynamic import:');
import('lightweight-charts').then(module => {
  console.log('- Import successful!');
  console.log('- createChart available:', typeof module.createChart);
  console.log('- Module keys:', Object.keys(module));

  // Try creating a test chart
  if (typeof module.createChart === 'function') {
    console.log('- createChart is a function! ✅');

    // Test with a dummy container
    const testDiv = document.createElement('div');
    testDiv.style.width = '400px';
    testDiv.style.height = '300px';

    try {
      const testChart = module.createChart(testDiv, { width: 400, height: 300 });
      console.log('- Test chart created:', testChart);
      console.log('- addCandlestickSeries available:', typeof testChart.addCandlestickSeries);
    } catch (error) {
      console.error('- Test chart creation failed:', error);
    }
  } else {
    console.error('- createChart is not a function! ❌');
  }
}).catch(error => {
  console.error('- Import failed:', error);
});

console.log('=== End Debug Script ===');