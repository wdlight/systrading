'use client';

export default function TestPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">테스트 페이지</h1>
      <p className="text-gray-600">이 페이지가 정상적으로 로드되면 기본적인 Next.js는 문제없이 작동합니다.</p>
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded">
        <p className="text-blue-800">현재 시간: {new Date().toLocaleString()}</p>
      </div>
    </div>
  );
}