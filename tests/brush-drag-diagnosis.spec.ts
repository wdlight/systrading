/**
 * Brush 드래그 이벤트 진단 테스트
 * Playwright를 사용하여 Brush 컴포넌트의 드래그 동작을 검증
 */

import { test, expect } from '@playwright/test';

test.describe('Brush 드래그 이벤트 진단', () => {
  test.beforeEach(async ({ page }) => {
    // 디버그 페이지로 이동
    await page.goto('http://localhost:9000/debug-brush');
    
    // 페이지 로딩 대기 (차트 데이터 로드)
    await page.waitForTimeout(5000);
  });

  test('1. Brush 컴포넌트 존재 확인', async ({ page }) => {
    console.log('\n=== 테스트 1: Brush 컴포넌트 존재 확인 ===');
    
    // Recharts Brush 클래스 찾기
    const brushElement = page.locator('.recharts-brush');
    const brushCount = await brushElement.count();
    
    console.log(`✓ Brush 요소 개수: ${brushCount}`);
    
    if (brushCount > 0) {
      // Brush의 속성 확인
      const brushBox = await brushElement.boundingBox();
      console.log('✓ Brush 위치 및 크기:', brushBox);
      
      // 스크린샷 저장
      await page.screenshot({ 
        path: '/tmp/brush-element.png',
        fullPage: true 
      });
      console.log('✓ 스크린샷 저장: /tmp/brush-element.png');
    } else {
      console.log('❌ Brush 요소를 찾을 수 없습니다!');
    }
    
    expect(brushCount).toBeGreaterThan(0);
  });

  test('2. Brush 하위 요소 분석', async ({ page }) => {
    console.log('\n=== 테스트 2: Brush 하위 요소 분석 ===');
    
    // Brush 관련 모든 요소 찾기
    const brushSlider = page.locator('.recharts-brush-slider');
    const brushTraveller = page.locator('.recharts-brush-traveller');
    const brushTexts = page.locator('.recharts-brush text');
    
    console.log(`✓ Brush Slider: ${await brushSlider.count()}개`);
    console.log(`✓ Brush Traveller: ${await brushTraveller.count()}개`);
    console.log(`✓ Brush Text: ${await brushTexts.count()}개`);
    
    // 각 요소의 위치 확인
    if (await brushSlider.count() > 0) {
      const sliderBox = await brushSlider.first().boundingBox();
      console.log('✓ Slider 위치:', sliderBox);
    }
    
    if (await brushTraveller.count() > 0) {
      const travellerCount = await brushTraveller.count();
      for (let i = 0; i < travellerCount; i++) {
        const box = await brushTraveller.nth(i).boundingBox();
        console.log(`✓ Traveller ${i} 위치:`, box);
      }
    }
  });

  test('3. Brush 드래그 시뮬레이션 (Slider)', async ({ page }) => {
    console.log('\n=== 테스트 3: Brush Slider 드래그 ===');
    
    const brushSlider = page.locator('.recharts-brush-slider');
    
    if (await brushSlider.count() > 0) {
      const slider = brushSlider.first();
      const box = await slider.boundingBox();
      
      if (box) {
        console.log('✓ Slider 초기 위치:', box);
        
        // 왼쪽으로 드래그 시뮬레이션
        const startX = box.x + box.width / 2;
        const startY = box.y + box.height / 2;
        const endX = startX - 200; // 왼쪽으로 200px 이동
        
        console.log(`✓ 드래그 시작: (${startX}, ${startY})`);
        console.log(`✓ 드래그 종료: (${endX}, ${startY})`);
        
        // 콘솔 로그 캡처
        const logs: string[] = [];
        page.on('console', msg => {
          if (msg.text().includes('Brush') || msg.text().includes('🔥')) {
            logs.push(msg.text());
            console.log('📋 콘솔:', msg.text());
          }
        });
        
        // 드래그 실행
        await page.mouse.move(startX, startY);
        await page.mouse.down();
        await page.mouse.move(endX, startY, { steps: 10 });
        await page.mouse.up();
        
        // 이벤트 발생 대기
        await page.waitForTimeout(1000);
        
        console.log(`✓ 캡처된 로그 개수: ${logs.length}`);
        
        // 스크린샷
        await page.screenshot({ 
          path: '/tmp/brush-after-drag.png',
          fullPage: true 
        });
        console.log('✓ 드래그 후 스크린샷: /tmp/brush-after-drag.png');
        
        if (logs.length > 0) {
          console.log('✅ Brush 이벤트 발생 확인!');
        } else {
          console.log('❌ Brush 이벤트가 발생하지 않았습니다.');
        }
      }
    } else {
      console.log('❌ Brush Slider를 찾을 수 없습니다.');
    }
  });

  test('4. Brush 드래그 시뮬레이션 (Traveller)', async ({ page }) => {
    console.log('\n=== 테스트 4: Brush Traveller 드래그 ===');
    
    const brushTraveller = page.locator('.recharts-brush-traveller');
    
    if (await brushTraveller.count() >= 2) {
      // 왼쪽 Traveller (첫 번째)
      const leftTraveller = brushTraveller.first();
      const box = await leftTraveller.boundingBox();
      
      if (box) {
        console.log('✓ 왼쪽 Traveller 초기 위치:', box);
        
        const startX = box.x + box.width / 2;
        const startY = box.y + box.height / 2;
        const endX = startX - 150; // 왼쪽으로 150px 이동
        
        console.log(`✓ 드래그 시작: (${startX}, ${startY})`);
        console.log(`✓ 드래그 종료: (${endX}, ${startY})`);
        
        // 콘솔 로그 캡처
        const logs: string[] = [];
        page.on('console', msg => {
          if (msg.text().includes('Brush') || msg.text().includes('🔥')) {
            logs.push(msg.text());
            console.log('📋 콘솔:', msg.text());
          }
        });
        
        // 드래그 실행
        await page.mouse.move(startX, startY);
        await page.mouse.down();
        await page.mouse.move(endX, startY, { steps: 10 });
        await page.mouse.up();
        
        await page.waitForTimeout(1000);
        
        console.log(`✓ 캡처된 로그 개수: ${logs.length}`);
        
        if (logs.length > 0) {
          console.log('✅ Traveller 드래그 이벤트 발생!');
        } else {
          console.log('❌ Traveller 드래그 이벤트가 발생하지 않았습니다.');
        }
      }
    } else {
      console.log('❌ Brush Traveller를 찾을 수 없습니다.');
    }
  });

  test('5. 이벤트 로그 UI 확인', async ({ page }) => {
    console.log('\n=== 테스트 5: 이벤트 로그 UI 확인 ===');
    
    // "Brush 이벤트 로그" 섹션 확인
    const logSection = page.locator('text=🔍 Brush 이벤트 로그');
    const exists = await logSection.count() > 0;
    
    console.log(`✓ 이벤트 로그 섹션 존재: ${exists}`);
    
    if (exists) {
      // 초기 메시지 확인
      const emptyMessage = page.locator('text=아직 Brush 이벤트가 발생하지 않았습니다');
      const hasEmptyMessage = await emptyMessage.count() > 0;
      
      console.log(`✓ 초기 안내 메시지 표시: ${hasEmptyMessage}`);
      
      // 디버그 정보 섹션 확인
      const debugSection = page.locator('text=🔧 디버그 정보');
      const hasDebugSection = await debugSection.count() > 0;
      
      console.log(`✓ 디버그 정보 섹션 존재: ${hasDebugSection}`);
    }
    
    expect(exists).toBe(true);
  });

  test('6. 차트 데이터 로드 확인', async ({ page }) => {
    console.log('\n=== 테스트 6: 차트 데이터 확인 ===');
    
    // 캔들 개수 확인
    const candleCount = page.locator('text=/\\d+개 캔들/');
    const candleText = await candleCount.first().textContent();
    
    console.log(`✓ 캔들 데이터: ${candleText}`);
    
    // 차트 SVG 확인
    const chartSvg = page.locator('svg.recharts-surface');
    const svgCount = await chartSvg.count();
    
    console.log(`✓ Chart SVG 개수: ${svgCount}`);
    
    if (svgCount > 0) {
      const svgBox = await chartSvg.first().boundingBox();
      console.log('✓ Chart 크기:', svgBox);
    }
  });

  test('7. DOM 구조 전체 분석', async ({ page }) => {
    console.log('\n=== 테스트 7: DOM 구조 분석 ===');
    
    // Recharts 관련 모든 클래스 찾기
    const rechartsElements = await page.locator('[class*="recharts"]').all();
    
    console.log(`✓ 총 Recharts 요소 개수: ${rechartsElements.length}`);
    
    // 클래스 이름별 그룹화
    const classNames = new Map<string, number>();
    
    for (const element of rechartsElements) {
      const className = await element.getAttribute('class');
      if (className) {
        const classes = className.split(' ');
        for (const cls of classes) {
          if (cls.startsWith('recharts-')) {
            classNames.set(cls, (classNames.get(cls) || 0) + 1);
          }
        }
      }
    }
    
    console.log('\n✓ Recharts 클래스 분포:');
    Array.from(classNames.entries())
      .sort((a, b) => b[1] - a[1])
      .forEach(([className, count]) => {
        console.log(`   ${className}: ${count}개`);
      });
    
    // HTML 구조 저장
    const brushHtml = await page.locator('.recharts-brush').first().innerHTML().catch(() => 'Not found');
    console.log('\n✓ Brush HTML 구조:');
    console.log(brushHtml.substring(0, 500));
  });
});
