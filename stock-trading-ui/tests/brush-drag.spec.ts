import { test, expect } from '@playwright/test';

test.describe('Brush 드래그 진단', () => {
  test('Brush 컴포넌트 및 드래그 이벤트 확인', async ({ page }) => {
    console.log('=== Brush 드래그 진단 시작 ===\n');
    
    // 페이지 이동
    await page.goto('http://localhost:9000/debug-brush');
    console.log('✓ 페이지 로드: http://localhost:9000/debug-brush');
    
    // 데이터 로딩 대기
    await page.waitForTimeout(5000);
    console.log('✓ 데이터 로딩 대기 완료\n');
    
    // 1. Brush 요소 확인
    console.log('--- 1. Brush 요소 확인 ---');
    const brushElements = await page.locator('[class*="recharts-brush"]').all();
    console.log(`Brush 관련 요소: ${brushElements.length}개`);
    
    for (let i = 0; i < brushElements.length; i++) {
      const className = await brushElements[i].getAttribute('class');
      const box = await brushElements[i].boundingBox();
      console.log(`  [${i}] class="${className}"`);
      console.log(`      위치: ${JSON.stringify(box)}`);
    }
    
    // 2. Brush Slider 확인
    console.log('\n--- 2. Brush Slider 확인 ---');
    const slider = page.locator('.recharts-brush-slider').first();
    const sliderExists = await slider.count() > 0;
    console.log(`Brush Slider 존재: ${sliderExists}`);
    
    if (sliderExists) {
      const sliderBox = await slider.boundingBox();
      console.log(`Slider 위치: ${JSON.stringify(sliderBox)}`);
    }
    
    // 3. Brush Traveller 확인
    console.log('\n--- 3. Brush Traveller 확인 ---');
    const travellers = await page.locator('.recharts-brush-traveller').all();
    console.log(`Traveller 개수: ${travellers.length}개`);
    
    for (let i = 0; i < travellers.length; i++) {
      const box = await travellers[i].boundingBox();
      console.log(`  Traveller[${i}]: ${JSON.stringify(box)}`);
    }
    
    // 스크린샷 저장
    await page.screenshot({ path: '/tmp/brush-before-drag.png', fullPage: true });
    console.log('\n✓ 초기 스크린샷 저장: /tmp/brush-before-drag.png');
    
    // 4. 드래그 시뮬레이션
    console.log('\n--- 4. 드래그 시뮬레이션 ---');
    
    if (sliderExists) {
      const sliderBox = await slider.boundingBox();
      
      if (sliderBox) {
        const startX = sliderBox.x + sliderBox.width * 0.7;
        const startY = sliderBox.y + sliderBox.height / 2;
        const endX = sliderBox.x + sliderBox.width * 0.2;
        
        console.log(`드래그 시작: (${Math.round(startX)}, ${Math.round(startY)})`);
        console.log(`드래그 종료: (${Math.round(endX)}, ${Math.round(startY)})`);
        console.log(`드래그 거리: ${Math.round(startX - endX)}px 왼쪽으로`);
        
        // 콘솔 메시지 캡처
        const consoleLogs: string[] = [];
        page.on('console', msg => {
          const text = msg.text();
          consoleLogs.push(text);
          if (text.includes('Brush') || text.includes('🔥') || text.includes('[RechartsAdapter]')) {
            console.log(`  📋 콘솔: ${text}`);
          }
        });
        
        // 드래그 실행
        console.log('\n드래그 실행 중...');
        await page.mouse.move(startX, startY);
        await page.waitForTimeout(200);
        await page.mouse.down();
        await page.waitForTimeout(200);
        await page.mouse.move(endX, startY, { steps: 20 });
        await page.waitForTimeout(200);
        await page.mouse.up();
        await page.waitForTimeout(1000);
        
        // 드래그 후 스크린샷
        await page.screenshot({ path: '/tmp/brush-after-drag.png', fullPage: true });
        console.log('✓ 드래그 후 스크린샷 저장: /tmp/brush-after-drag.png');
        
        // 이벤트 로그 확인
        console.log('\n--- 5. 이벤트 로그 확인 ---');
        const eventLogs = page.locator('.bg-green-900\\/20');
        const greenLogCount = await eventLogs.count();
        console.log(`녹색 하이라이트 로그 (startIndex < 20): ${greenLogCount}개`);
        
        const allEventLogs = page.locator('text=startIndex:').locator('..');
        const totalLogs = await allEventLogs.count();
        console.log(`전체 이벤트 로그: ${totalLogs}개`);
        
        // 결과 판정
        console.log('\n=== 결과 ===');
        const brushEventLogged = consoleLogs.some(log => 
          log.includes('🔥 Brush Event') || log.includes('[RechartsAdapter] Brush changed')
        );
        
        if (brushEventLogged) {
          console.log('✅ Brush 이벤트 발생 확인!');
        } else {
          console.log('❌ Brush 이벤트가 발생하지 않았습니다.');
          console.log('\n캡처된 콘솔 로그:');
          consoleLogs.slice(0, 20).forEach(log => console.log(`  ${log}`));
        }
        
        if (totalLogs > 0) {
          console.log('✅ UI에 이벤트 로그 표시됨');
        } else {
          console.log('❌ UI에 이벤트 로그가 표시되지 않음');
        }
      }
    } else {
      console.log('❌ Brush Slider를 찾을 수 없어 드래그 테스트를 건너뜁니다.');
    }
  });
});
