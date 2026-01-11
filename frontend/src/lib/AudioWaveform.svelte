<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  export let duration: number; // 音声の長さ（秒）
  export let width: number = 200; // 波形の幅（ピクセル）
  export let height: number = 40; // 波形の高さ（ピクセル）
  export let audioUrl: string | null = null; // 実際の音声ファイルURL（オプション）
  export let color: string = "#667eea"; // 波形の色

  let canvas: HTMLCanvasElement;
  let audioContext: AudioContext | null = null;
  let waveformData: number[] = [];

  // 音声ファイルから波形データを取得
  async function loadAudioWaveform(url: string): Promise<number[]> {
    try {
      if (!audioContext) {
        audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      }

      const response = await fetch(url);
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      // 波形データを抽出（簡易版：RMS値を使用）
      const channelData = audioBuffer.getChannelData(0);
      const samples = 100; // 波形のポイント数
      const blockSize = Math.floor(channelData.length / samples);
      const waveform: number[] = [];

      for (let i = 0; i < samples; i++) {
        let sum = 0;
        const start = i * blockSize;
        const end = Math.min(start + blockSize, channelData.length);

        for (let j = start; j < end; j++) {
          sum += Math.abs(channelData[j]);
        }

        waveform.push(sum / blockSize);
      }

      // 正規化（0-1の範囲に）
      const max = Math.max(...waveform);
      return waveform.map(v => max > 0 ? v / max : 0);
    } catch (error) {
      console.error("音声波形の読み込みエラー:", error);
      return generateSimulatedWaveform();
    }
  }

  // シミュレートされた波形を生成（テキストベースの推定）
  function generateSimulatedWaveform(): number[] {
    const samples = 100;
    const waveform: number[] = [];

    // ランダムな波形を生成（実際の音声に近いパターン）
    for (let i = 0; i < samples; i++) {
      // 正弦波ベースのパターンにノイズを追加
      const base = Math.sin((i / samples) * Math.PI * 4) * 0.5 + 0.5;
      const noise = (Math.random() - 0.5) * 0.3;
      const value = Math.max(0.1, Math.min(1.0, base + noise));
      waveform.push(value);
    }

    return waveform;
  }

  // 波形を描画
  function drawWaveform() {
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // キャンバスをクリア
    ctx.clearRect(0, 0, width, height);

    if (waveformData.length === 0) return;

    // 背景
    ctx.fillStyle = "#f3f4f6";
    ctx.fillRect(0, 0, width, height);

    // 波形を描画
    ctx.fillStyle = color;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;

    const centerY = height / 2;
    const stepX = width / waveformData.length;

    // パスを開始
    ctx.beginPath();
    ctx.moveTo(0, centerY);

    for (let i = 0; i < waveformData.length; i++) {
      const x = i * stepX;
      const amplitude = waveformData[i] * (height / 2 - 4); // 少し余白を残す
      const y1 = centerY - amplitude;
      const y2 = centerY + amplitude;

      // 上下対称の波形
      if (i === 0) {
        ctx.moveTo(x, y1);
      } else {
        ctx.lineTo(x, y1);
      }
    }

    // 下半分
    for (let i = waveformData.length - 1; i >= 0; i--) {
      const x = i * stepX;
      const amplitude = waveformData[i] * (height / 2 - 4);
      const y2 = centerY + amplitude;
      ctx.lineTo(x, y2);
    }

    ctx.closePath();
    ctx.fill();

    // 中央線
    ctx.strokeStyle = "#9ca3af";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(width, centerY);
    ctx.stroke();
  }

  // 波形データを読み込む
  async function loadWaveformData() {
    if (audioUrl) {
      // 実際の音声ファイルから波形を読み込む
      waveformData = await loadAudioWaveform(audioUrl);
    } else {
      // シミュレートされた波形を生成
      waveformData = generateSimulatedWaveform();
    }
    drawWaveform();
  }

  // 初期化
  onMount(async () => {
    await loadWaveformData();
  });

  // audioUrlが変更されたら再読み込み
  $: if (audioUrl !== undefined) {
    loadWaveformData();
  }

  // 波形データが変更されたら再描画
  $: if (waveformData.length > 0 && canvas) {
    drawWaveform();
  }

  // クリーンアップ
  onDestroy(() => {
    if (audioContext) {
      audioContext.close();
    }
  });
</script>

<canvas
  bind:this={canvas}
  width={width}
  height={height}
  class="audio-waveform"
></canvas>

<style>
  .audio-waveform {
    display: block;
    border-radius: 4px;
  }
</style>
