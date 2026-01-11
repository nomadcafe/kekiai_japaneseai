<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import AudioWaveform from "./AudioWaveform.svelte";

  export let dialogueData: Record<string, Array<{ speaker: string; text: string }>>;
  export let slides: Array<{ slide_number: number; url: string }>;
  export let currentJobMetadata: any;
  export let jobId: string | null = null; // ジョブID（音声ファイル取得用）
  export let onUpdate: (data: Record<string, Array<{ speaker: string; text: string }>>) => void;

  // タイムライン設定
  let pixelsPerSecond = 50; // 1秒あたりのピクセル数
  let timelineStartTime = 0; // タイムラインの開始時間（秒）
  let timelineEndTime = 300; // タイムラインの終了時間（秒、デフォルト5分）
  let currentTime = 0; // 現在の再生位置
  let isPlaying = false;
  let isDragging = false;
  let dragTarget: { type: 'dialogue' | 'slide', slideKey: string, index: number } | null = null;
  let dragStartX = 0;
  let dragStartTime = 0;

  // 計算された時間情報
  interface TimelineSegment {
    slideKey: string;
    slideNumber: number;
    startTime: number;
    endTime: number;
    dialogues: Array<{
      speaker: string;
      text: string;
      startTime: number;
      endTime: number;
      duration: number;
    }>;
  }

  let timelineSegments: TimelineSegment[] = [];

  // 音声の推定時間を計算（簡易版：文字数ベース）
  function estimateAudioDuration(text: string, speaker: string): number {
    // 日本語の平均読み上げ速度：約4文字/秒
    const charsPerSecond = 4;
    const baseDuration = text.length / charsPerSecond;
    
    // 最小・最大時間の制限
    const minDuration = 1.0;
    const maxDuration = 10.0;
    
    return Math.max(minDuration, Math.min(maxDuration, baseDuration));
  }

  // タイムラインセグメントを計算
  function calculateTimelineSegments() {
    const segments: TimelineSegment[] = [];
    let currentTime = 0;
    const pauseBetweenDialogues = 0.5; // 対話間の間隔（秒）
    const pauseBetweenSlides = 1.0; // スライド間の間隔（秒）

    const slideKeys = Object.keys(dialogueData).sort((a, b) => {
      const numA = parseInt(a.split("_")[1]);
      const numB = parseInt(b.split("_")[1]);
      return numA - numB;
    });

    slideKeys.forEach((slideKey, slideIndex) => {
      const slideNum = parseInt(slideKey.split("_")[1]);
      const dialogues = dialogueData[slideKey] || [];
      const slideStartTime = currentTime;

      const dialogueSegments = dialogues.map((dialogue, index) => {
        const duration = estimateAudioDuration(dialogue.text, dialogue.speaker);
        const startTime = currentTime;
        const endTime = currentTime + duration;
        currentTime = endTime + pauseBetweenDialogues;

        return {
          speaker: dialogue.speaker,
          text: dialogue.text,
          startTime,
          endTime,
          duration
        };
      });

      const slideEndTime = dialogueSegments.length > 0 
        ? dialogueSegments[dialogueSegments.length - 1].endTime
        : slideStartTime + 3.0; // デフォルト3秒

      segments.push({
        slideKey,
        slideNumber: slideNum,
        startTime: slideStartTime,
        endTime: slideEndTime,
        dialogues: dialogueSegments
      });

      // スライド間の間隔
      if (slideIndex < slideKeys.length - 1) {
        currentTime = slideEndTime + pauseBetweenSlides;
      }
    });

    timelineSegments = segments;
    timelineEndTime = Math.max(timelineEndTime, currentTime + 10); // 余裕を持たせる
  }

  // 時間をピクセル位置に変換
  function timeToPixel(time: number): number {
    return (time - timelineStartTime) * pixelsPerSecond;
  }

  // ピクセル位置を時間に変換
  function pixelToTime(pixel: number): number {
    return timelineStartTime + pixel / pixelsPerSecond;
  }

  // 時間をフォーマット（MM:SS）
  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  // ドラッグ開始
  function handleDragStart(event: MouseEvent, type: 'dialogue' | 'slide', slideKey: string, index: number) {
    isDragging = true;
    dragTarget = { type, slideKey, index };
    
    const container = document.querySelector('.timeline-container');
    if (container) {
      const rect = container.getBoundingClientRect();
      // コンテナ内の相対位置を保存
      dragStartX = event.clientX - rect.left;
    } else {
      dragStartX = event.clientX;
    }
    
    const segment = timelineSegments.find(s => s.slideKey === slideKey);
    if (segment) {
      if (type === 'dialogue' && segment.dialogues[index]) {
        dragStartTime = segment.dialogues[index].startTime;
      } else if (type === 'slide') {
        dragStartTime = segment.startTime;
      }
    }

    event.preventDefault();
    event.stopPropagation();
  }

  // ドラッグ中
  function handleDragMove(event: MouseEvent) {
    if (!isDragging || !dragTarget) return;

    const container = document.querySelector('.timeline-container');
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const relativeX = event.clientX - rect.left;
    const deltaX = relativeX - dragStartX;
    const deltaTime = deltaX / pixelsPerSecond;
    const newTime = dragStartTime + deltaTime;

    // 時間の制限（0秒以上）
    if (newTime < 0) return;

    const segment = timelineSegments.find(s => s.slideKey === dragTarget.slideKey);
    if (!segment) return;

    if (dragTarget.type === 'dialogue' && segment.dialogues[dragTarget.index]) {
      const dialogue = segment.dialogues[dragTarget.index];
      const duration = dialogue.endTime - dialogue.startTime;
      dialogue.startTime = Math.max(0, newTime);
      dialogue.endTime = dialogue.startTime + duration;
      
      // 前の対話との間隔を調整
      if (dragTarget.index > 0) {
        const prevDialogue = segment.dialogues[dragTarget.index - 1];
        if (dialogue.startTime < prevDialogue.endTime + 0.5) {
          dialogue.startTime = prevDialogue.endTime + 0.5;
          dialogue.endTime = dialogue.startTime + duration;
        }
      }
      
      // 次の対話との間隔を調整
      if (dragTarget.index < segment.dialogues.length - 1) {
        const nextDialogue = segment.dialogues[dragTarget.index + 1];
        if (dialogue.endTime > nextDialogue.startTime - 0.5) {
          nextDialogue.startTime = dialogue.endTime + 0.5;
          nextDialogue.endTime = nextDialogue.startTime + (nextDialogue.endTime - nextDialogue.startTime);
        }
      }
    } else if (dragTarget.type === 'slide') {
      segment.startTime = Math.max(0, newTime);
      const duration = segment.endTime - segment.startTime;
      segment.endTime = segment.startTime + duration;
    }

    // リアクティブ更新のため
    timelineSegments = [...timelineSegments];
  }

  // ドラッグ終了
  function handleDragEnd() {
    isDragging = false;
    dragTarget = null;
    updateDialogueData();
  }

  // タイムラインを再計算
  function recalculateTimeline() {
    // スライドの順序を維持しながら時間を再調整
    let currentTime = 0;
    const pauseBetweenDialogues = 0.5;
    const pauseBetweenSlides = 1.0;

    timelineSegments.forEach((segment, slideIndex) => {
      segment.startTime = currentTime;
      
      segment.dialogues.forEach((dialogue, index) => {
        dialogue.startTime = currentTime;
        dialogue.endTime = currentTime + dialogue.duration;
        currentTime = dialogue.endTime + pauseBetweenDialogues;
      });

      segment.endTime = segment.dialogues.length > 0
        ? segment.dialogues[segment.dialogues.length - 1].endTime
        : segment.startTime + 3.0;

      if (slideIndex < timelineSegments.length - 1) {
        currentTime = segment.endTime + pauseBetweenSlides;
      }
    });

    timelineEndTime = Math.max(timelineEndTime, currentTime + 10);
  }

  // 対話データを更新
  function updateDialogueData() {
    // タイムラインの変更をdialogueDataに反映
    // この実装では、時間の変更は保持するが、テキストは変更しない
    if (onUpdate) {
      onUpdate(dialogueData);
    }
  }

  // 時間を直接編集
  function updateDialogueTime(slideKey: string, index: number, newStartTime: number, newDuration: number) {
    const segment = timelineSegments.find(s => s.slideKey === slideKey);
    if (segment && segment.dialogues[index]) {
      segment.dialogues[index].startTime = newStartTime;
      segment.dialogues[index].duration = newDuration;
      segment.dialogues[index].endTime = newStartTime + newDuration;
      recalculateTimeline();
      updateDialogueData();
    }
  }

  // スライドの時間を直接編集
  function updateSlideTime(slideKey: string, newStartTime: number, newDuration: number) {
    const segment = timelineSegments.find(s => s.slideKey === slideKey);
    if (segment) {
      segment.startTime = newStartTime;
      segment.endTime = newStartTime + newDuration;
      recalculateTimeline();
      updateDialogueData();
    }
  }

  // 初期化
  onMount(() => {
    calculateTimelineSegments();
    
    // グローバルマウスイベント
    const handleMouseMove = (e: MouseEvent) => handleDragMove(e);
    const handleMouseUp = () => handleDragEnd();
    
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  });

  // dialogueDataが変更されたら再計算
  $: if (dialogueData) {
    calculateTimelineSegments();
  }
</script>

<div class="timeline-editor">
  <div class="timeline-header">
    <h3>⏱️ タイムラインエディター</h3>
    <div class="timeline-controls">
      <label>
        ズーム:
        <input
          type="range"
          min="20"
          max="100"
          step="10"
          bind:value={pixelsPerSecond}
        />
        {pixelsPerSecond}px/秒
      </label>
      <div class="time-display">
        総時間: {formatTime(timelineEndTime)}
      </div>
    </div>
  </div>

  <div class="timeline-container" on:mousemove={handleDragMove} on:mouseup={handleDragEnd}>
    <!-- 時間軸ラベル -->
    <div class="timeline-ruler">
      {#each Array(Math.ceil((timelineEndTime - timelineStartTime) / 10) + 1) as _, i}
        {@const time = i * 10}
        <div
          class="ruler-mark"
          style="left: {timeToPixel(time)}px"
        >
          <span class="ruler-label">{formatTime(time)}</span>
        </div>
      {/each}
    </div>

    <!-- タイムラインセグメント -->
    <div class="timeline-tracks">
      {#each timelineSegments as segment}
        <div class="timeline-track">
          <!-- スライドセグメント -->
          <div
            class="slide-segment"
            style="left: {timeToPixel(segment.startTime)}px; width: {timeToPixel(segment.endTime - segment.startTime)}px"
            on:mousedown={(e) => handleDragStart(e, 'slide', segment.slideKey, 0)}
          >
            <div class="slide-segment-header">
              {#if slides.find(s => s.slide_number === segment.slideNumber)}
                {@const slide = slides.find(s => s.slide_number === segment.slideNumber)}
                <img
                  src={slide.url}
                  alt="Slide {segment.slideNumber}"
                  class="slide-thumbnail-small"
                />
              {/if}
              <span class="slide-label">スライド {segment.slideNumber}</span>
              <span class="slide-duration">
                {formatTime(segment.endTime - segment.startTime)}
              </span>
            </div>
          </div>

          <!-- 対話セグメント -->
          {#each segment.dialogues as dialogue, index}
            {@const audioFilename = `slide_${segment.slideNumber.toString().padStart(3, '0')}_${(index + 1).toString().padStart(3, '0')}_${dialogue.speaker}.wav`}
            {@const audioUrl = jobId ? `/api/jobs/${jobId}/audio/${audioFilename}` : null}
            <div
              class="dialogue-segment {dialogue.speaker}"
              style="left: {timeToPixel(dialogue.startTime)}px; width: {timeToPixel(dialogue.duration)}px"
              on:mousedown={(e) => handleDragStart(e, 'dialogue', segment.slideKey, index)}
            >
              <div class="dialogue-segment-content">
                <div class="dialogue-speaker">
                  {dialogue.speaker === "speaker1"
                    ? (currentJobMetadata?.speaker1?.name || "話者1")
                    : (currentJobMetadata?.speaker2?.name || "話者2")}
                </div>
                <!-- 音声波形 -->
                <div class="dialogue-waveform">
                  <AudioWaveform
                    duration={dialogue.duration}
                    width={Math.max(100, timeToPixel(dialogue.duration) - 20)}
                    height={20}
                    audioUrl={audioUrl}
                    color={dialogue.speaker === "speaker1" ? "#667eea" : "#f5576c"}
                  />
                </div>
                <div class="dialogue-text-preview" title={dialogue.text}>
                  {dialogue.text.length > 30
                    ? dialogue.text.substring(0, 30) + "..."
                    : dialogue.text}
                </div>
                <div class="dialogue-time">
                  {formatTime(dialogue.startTime)} - {formatTime(dialogue.endTime)}
                </div>
              </div>
              
              <!-- 時間編集コントロール -->
              <div class="dialogue-time-controls">
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={dialogue.startTime.toFixed(1)}
                  on:change={(e) => {
                    const newStart = parseFloat(e.currentTarget.value);
                    updateDialogueTime(segment.slideKey, index, newStart, dialogue.duration);
                  }}
                  class="time-input"
                />
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  max="10"
                  value={dialogue.duration.toFixed(1)}
                  on:change={(e) => {
                    const newDuration = parseFloat(e.currentTarget.value);
                    updateDialogueTime(segment.slideKey, index, dialogue.startTime, newDuration);
                  }}
                  class="duration-input"
                />
              </div>
            </div>
          {/each}
        </div>
      {/each}
    </div>

    <!-- 現在位置インジケーター -->
    {#if isPlaying}
      <div
        class="playhead"
        style="left: {timeToPixel(currentTime)}px"
      ></div>
    {/if}
  </div>

  <div class="timeline-legend">
    <div class="legend-item">
      <div class="legend-color speaker1"></div>
      <span>話者1</span>
    </div>
    <div class="legend-item">
      <div class="legend-color speaker2"></div>
      <span>話者2</span>
    </div>
    <div class="legend-hint">
      💡 ヒント: セグメントをドラッグして時間を調整できます
    </div>
  </div>
</div>

<style>
  .timeline-editor {
    width: 100%;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
  }

  .timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #dee2e6;
  }

  .timeline-header h3 {
    margin: 0;
    color: #495057;
  }

  .timeline-controls {
    display: flex;
    gap: 20px;
    align-items: center;
  }

  .timeline-controls label {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
  }

  .timeline-controls input[type="range"] {
    width: 150px;
  }

  .time-display {
    font-weight: bold;
    color: #007bff;
  }

  .timeline-container {
    position: relative;
    width: 100%;
    min-height: 400px;
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    overflow-x: auto;
    overflow-y: visible;
    padding: 20px 0;
  }

  .timeline-ruler {
    position: relative;
    height: 30px;
    border-bottom: 2px solid #495057;
    margin-bottom: 10px;
  }

  .ruler-mark {
    position: absolute;
    top: 0;
    height: 100%;
    border-left: 1px solid #adb5bd;
  }

  .ruler-label {
    position: absolute;
    top: 5px;
    left: 5px;
    font-size: 11px;
    color: #6c757d;
  }

  .timeline-tracks {
    position: relative;
    min-height: 300px;
  }

  .timeline-track {
    position: relative;
    margin-bottom: 60px;
    min-height: 80px;
  }

  .slide-segment {
    position: absolute;
    top: 0;
    height: 40px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: 2px solid #5a67d8;
    border-radius: 4px;
    cursor: move;
    display: flex;
    align-items: center;
    padding: 5px 10px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .slide-segment:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    z-index: 10;
  }

  .slide-segment-header {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
  }

  .slide-thumbnail-small {
    width: 30px;
    height: 20px;
    object-fit: cover;
    border-radius: 2px;
  }

  .slide-label {
    font-weight: bold;
    color: white;
    font-size: 12px;
  }

  .slide-duration {
    margin-left: auto;
    color: white;
    font-size: 11px;
    opacity: 0.9;
  }

  .dialogue-segment {
    position: absolute;
    top: 50px;
    height: 60px;
    border-radius: 4px;
    cursor: move;
    border: 2px solid;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: box-shadow 0.2s;
  }

  .dialogue-segment:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    z-index: 10;
  }

  .dialogue-segment.speaker1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-color: #5a67d8;
  }

  .dialogue-segment.speaker2 {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    border-color: #e91e63;
  }

  .dialogue-segment-content {
    padding: 5px 8px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
  }

  .dialogue-waveform {
    margin: 2px 0;
    opacity: 0.8;
  }

  .dialogue-speaker {
    font-size: 10px;
    font-weight: bold;
    color: white;
    opacity: 0.9;
  }

  .dialogue-text-preview {
    font-size: 11px;
    color: white;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
  }

  .dialogue-time {
    font-size: 9px;
    color: white;
    opacity: 0.8;
  }

  .dialogue-time-controls {
    position: absolute;
    top: -25px;
    left: 0;
    display: flex;
    gap: 5px;
    opacity: 0;
    transition: opacity 0.2s;
  }

  .dialogue-segment:hover .dialogue-time-controls {
    opacity: 1;
  }

  .time-input,
  .duration-input {
    width: 60px;
    padding: 2px 4px;
    font-size: 10px;
    border: 1px solid #ced4da;
    border-radius: 2px;
  }

  .playhead {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #ff0000;
    z-index: 100;
    pointer-events: none;
  }

  .playhead::before {
    content: '';
    position: absolute;
    top: -5px;
    left: -5px;
    width: 12px;
    height: 12px;
    background: #ff0000;
    border-radius: 50%;
  }

  .timeline-legend {
    display: flex;
    gap: 20px;
    align-items: center;
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #dee2e6;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .legend-color {
    width: 20px;
    height: 20px;
    border-radius: 4px;
  }

  .legend-color.speaker1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  .legend-color.speaker2 {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }

  .legend-hint {
    margin-left: auto;
    font-size: 12px;
    color: #6c757d;
    font-style: italic;
  }
</style>
