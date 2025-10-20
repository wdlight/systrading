/**
 * 간단한 WebSocket 테스트 클라이언트
 * Backend WebSocket 서버에 직접 연결하여 메시지를 확인합니다.
 */

const WebSocket = require('ws');

const WS_URL = 'ws://localhost:8000/ws';
const TEST_STOCK_CODE = '005930'; // 삼성전자

console.log('🚀 WebSocket 테스트 시작\n');
console.log(`📡 연결 시도: ${WS_URL}\n`);

const ws = new WebSocket(WS_URL);

let messageCount = 0;
const receivedMessages = {
  minute_candle_update: [],
  minute_candle_finalize: [],
  other: []
};

ws.on('open', () => {
  console.log('✅ WebSocket 연결 성공!\n');

  // 삼성전자 구독 요청
  const subscribeMessage = {
    type: 'subscribe',
    stock_code: TEST_STOCK_CODE
  };

  console.log(`📤 구독 요청 전송: ${TEST_STOCK_CODE}\n`);
  ws.send(JSON.stringify(subscribeMessage));

  // 연결 유지 (ping)
  setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
    }
  }, 30000);

  console.log('⏳ 메시지 대기 중... (Ctrl+C로 종료)\n');
  console.log('=' .repeat(80) + '\n');
});

ws.on('message', (data) => {
  messageCount++;

  try {
    const message = JSON.parse(data.toString());
    const { type, stock_code, data: msgData } = message;

    // 타임스탬프 추가
    const timestamp = new Date().toISOString();

    // 메시지 타입별 분류
    if (type === 'minute_candle_update') {
      receivedMessages.minute_candle_update.push({ timestamp, message });

      console.log(`🔄 [${timestamp}] MINUTE_CANDLE_UPDATE`);
      console.log(`   종목: ${stock_code}`);
      console.log(`   시간: ${msgData?.timestamp}`);
      console.log(`   OHLCV: O=${msgData?.open} H=${msgData?.high} L=${msgData?.low} C=${msgData?.close} V=${msgData?.volume}`);
      console.log('');

    } else if (type === 'minute_candle_finalize') {
      receivedMessages.minute_candle_finalize.push({ timestamp, message });

      console.log(`🎉 [${timestamp}] MINUTE_CANDLE_FINALIZE ⭐⭐⭐`);
      console.log(`   종목: ${stock_code}`);
      console.log(`   시간: ${msgData?.timestamp}`);
      console.log(`   OHLCV: O=${msgData?.open} H=${msgData?.high} L=${msgData?.low} C=${msgData?.close} V=${msgData?.volume}`);
      console.log('   ✅ 이 분봉이 완성되어 캐시에 저장되었어야 합니다!');
      console.log('');

    } else {
      receivedMessages.other.push({ timestamp, message });

      // 기타 메시지는 요약만
      if (messageCount % 10 === 0 || type === 'connection_status') {
        console.log(`📨 [${timestamp}] ${type}`);
        if (type === 'connection_status') {
          console.log(`   상태: ${JSON.stringify(msgData)}`);
        }
        console.log('');
      }
    }

    // 통계 출력 (100개마다)
    if (messageCount % 100 === 0) {
      console.log('=' .repeat(80));
      console.log('📊 메시지 통계:');
      console.log(`   총 메시지: ${messageCount}개`);
      console.log(`   UPDATE: ${receivedMessages.minute_candle_update.length}개`);
      console.log(`   FINALIZE: ${receivedMessages.minute_candle_finalize.length}개`);
      console.log(`   기타: ${receivedMessages.other.length}개`);
      console.log('=' .repeat(80) + '\n');
    }

  } catch (error) {
    console.error('❌ 메시지 파싱 오류:', error.message);
    console.error('   원본 데이터:', data.toString().substring(0, 200));
  }
});

ws.on('error', (error) => {
  console.error('❌ WebSocket 오류:', error.message);
});

ws.on('close', (code, reason) => {
  console.log('\n' + '='.repeat(80));
  console.log('🔚 WebSocket 연결 종료');
  console.log(`   코드: ${code}`);
  console.log(`   사유: ${reason || '알 수 없음'}`);
  console.log('\n📊 최종 통계:');
  console.log(`   총 메시지: ${messageCount}개`);
  console.log(`   UPDATE: ${receivedMessages.minute_candle_update.length}개`);
  console.log(`   FINALIZE: ${receivedMessages.minute_candle_finalize.length}개`);
  console.log(`   기타: ${receivedMessages.other.length}개`);

  // 결과 파일 저장
  const fs = require('fs');
  const resultPath = '/home/wide/projects/systrading/websocket-test-result.json';

  const result = {
    testEndTime: new Date().toISOString(),
    totalMessages: messageCount,
    messagesByType: {
      update: receivedMessages.minute_candle_update.length,
      finalize: receivedMessages.minute_candle_finalize.length,
      other: receivedMessages.other.length
    },
    finalizeMessages: receivedMessages.minute_candle_finalize,
    lastUpdateMessages: receivedMessages.minute_candle_update.slice(-5),
    success: receivedMessages.minute_candle_finalize.length > 0
  };

  fs.writeFileSync(resultPath, JSON.stringify(result, null, 2));
  console.log(`\n💾 결과 저장: ${resultPath}`);

  if (receivedMessages.minute_candle_finalize.length > 0) {
    console.log('\n✅ 성공: FINALIZE 메시지를 수신했습니다!');
    console.log('   Frontend가 이 메시지를 받지 못했다면 Frontend 문제입니다.');
  } else {
    console.log('\n⚠️  경고: FINALIZE 메시지를 받지 못했습니다.');
    console.log('   1분 이상 대기하셨나요? 장 시간인가요?');
  }

  console.log('='.repeat(80) + '\n');
  process.exit(0);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n⏸️  사용자 중단...');
  ws.close(1000, 'User interrupted');
});

// 타임아웃 (5분)
setTimeout(() => {
  console.log('\n⏱️  타임아웃 (5분 경과)');
  ws.close(1000, 'Timeout');
}, 5 * 60 * 1000);
