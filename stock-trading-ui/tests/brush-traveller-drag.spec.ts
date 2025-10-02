import { test, expect } from '@playwright/test';

test('Brush Traveller 드래그 테스트', async ({ page }) => {
  console.log('=== Brush Traveller 드래그 테스트 ===\n');
  
  await page.goto('http://localhost:9000/debug-brush');
  console.log('✓ 페이지 로드');
  
  await page.waitForTimeout(5000);
  console.log('✓ 데이터 로딩 완료\n');
  
  // Traveller 찾기
  const travellers = await page.locator('.recharts-brush-traveller').all();
  console.log(`Traveller 개수: ${travellers.length}`);
  
  if (travellers.length >= 2) {
    // 왼쪽 Traveller 드래그
    const leftTraveller = travellers[0];
    const box = await leftTraveller.boundingBox();
    
    if (box) {
      console.log(`왼쪽 Traveller 위치: x=${box.x}, y=${box.y}, width=${box.width}, height=${box.height}`);
      
      const startX = box.x + box.width / 2;
      const startY = box.y + box.height / 2;
      const endX = box.x - 300; // 왼쪽으로 300px 이동
      
      console.log(`\n드래그: (${Math.round(startX)}, ${Math.round(startY)}) → (${Math.round(endX)}, ${Math.round(startY)})`);
      console.log(`거리: ${Math.round(startX - endX)}px 왼쪽`);
      
      // 콘솔 로그 캡처
      const logs: string[] = [];
      page.on('console', msg => {
        const text = msg.text();
        logs.push(text);
        if (text.includes('Brush') || text.includes('🔥')) {
          console.log(`📋 ${text}`);
        }
      });
      
      // 드래그 실행
      console.log('\n드래그 실행...');
      await page.mouse.move(startX, startY);
      await page.waitForTimeout(300);
      await page.mouse.down();
      await page.waitForTimeout(300);
      
      // 천천히 왼쪽으로 이동
      const steps = 30;
      for (let i = 1; i <= steps; i++) {
        const x = startX + (endX - startX) * (i / steps);
        await page.mouse.move(x, startY);
        await page.waitForTimeout(10);
      }
      
      await page.waitForTimeout(300);
      await page.mouse.up();
      await page.waitForTimeout(1500);
      
      console.log('✓ 드래그 완료\n');
      
      // 스크린샷
      await page.screenshot({ path: '/tmp/brush-traveller-drag.png', fullPage: true });
      console.log('✓ 스크린샷: /tmp/brush-traveller-drag.png\n');
      
      // 결과 확인
      console.log('=== 결과 분석 ===');
      const brushEvents = logs.filter(log => 
        log.includes('🔥 Brush Event') || log.includes('[RechartsAdapter] Brush changed')
      );
      
      console.log(`Brush 이벤트 발생 횟수: ${brushEvents.length}`);
      if (brushEvents.length > 0) {
        console.log('✅ SUCCESS: Brush 이벤트 발생!');
        brushEvents.forEach(log => console.log(`  ${log}`));
      } else {
        console.log('❌ FAIL: Brush 이벤트 미발생');
        console.log('\n전체 콘솔 로그 (최대 30개):');
        logs.slice(0, 30).forEach((log, i) => console.log(`  [${i}] ${log}`));
      }
      
      // UI 이벤트 로그 확인
      const uiLogs = await page.locator('[class*="startIndex"]').count();
      console.log(`\nUI 이벤트 로그 표시: ${uiLogs}개`);
    }
  }
});
