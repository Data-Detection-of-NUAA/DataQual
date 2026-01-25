<template>
  <el-form label-position="top">
    <!-- 变异增强策略：显示增强参数 -->
    <template v-if="strategyType === 'augmentation'">
      <!-- 图片类型参数 -->
      <template v-if="dataTypes.includes('image')">
        <el-divider content-position="left">图片增强参数</el-divider>
        <el-form-item label="噪声强度">
          <el-slider v-model="formData.image.noiseLevel" :min="0" :max="100" show-input />
          <span class="param-hint">添加噪声以提高模型鲁棒性</span>
        </el-form-item>
        <el-form-item label="模糊程度">
          <el-slider v-model="formData.image.blurRadius" :min="0" :max="10" show-input />
          <span class="param-hint">模拟不同的拍摄条件</span>
        </el-form-item>
        <el-form-item label="旋转角度">
          <el-slider v-model="formData.image.rotationAngle" :min="0" :max="360" show-input />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="formData.image.enableAdversarial">
            对抗样本生成
          </el-checkbox>
        </el-form-item>
      </template>

      <!-- 文本类型参数 -->
      <template v-if="dataTypes.includes('text')">
        <el-divider content-position="left">文本增强参数</el-divider>
        <el-form-item label="同义词替换比例">
          <el-slider v-model="formData.text.synonymReplaceRatio" :min="0" :max="100" show-input />
          <span class="param-hint">随机替换为同义词的比例</span>
        </el-form-item>
        <el-form-item label="回译语言">
          <el-select v-model="formData.text.backTranslationLang" style="width: 100%;">
            <el-option label="英语 → 中文 → 英语" value="en-zh-en" />
            <el-option label="中文 → 英语 → 中文" value="zh-en-zh" />
            <el-option label="日语 → 英语 → 日语" value="ja-en-ja" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="formData.text.enableParaphrase">
            释义改写
          </el-checkbox>
        </el-form-item>
      </template>

      <!-- 音频类型参数 -->
      <template v-if="dataTypes.includes('audio')">
        <el-divider content-position="left">音频增强参数</el-divider>
        <el-form-item label="音高变换范围">
          <el-slider v-model="formData.audio.pitchShiftRange" :min="-12" :max="12" show-input />
          <span class="param-hint">半音数量,正数升调,负数降调</span>
        </el-form-item>
        <el-form-item label="时间拉伸比例">
          <el-slider v-model="formData.audio.timeStretchRatio" :min="0.8" :max="1.2" :step="0.05" show-input />
          <span class="param-hint">改变播放速度但不改变音高</span>
        </el-form-item>
        <el-form-item label="背景噪声 SNR (dB)">
          <el-slider v-model="formData.audio.noiseSNR" :min="5" :max="30" show-input />
          <span class="param-hint">信噪比,值越高噪声越小</span>
        </el-form-item>
      </template>

      <!-- 变异增强策略通用参数 -->
      <el-form-item label="目标补入数量">
        <el-input-number
          v-model="formData.targetCount"
          :min="1"
          :max="10000"
          :step="100"
          style="width: 100%;"
        />
      </el-form-item>
    </template>

    <!-- 检索补数策略：只显示检索参数，不显示增强参数 -->
    <template v-if="strategyType === 'retrieval'">
      <el-divider content-position="left">检索参数</el-divider>
      <el-form-item label="数据源">
        <el-select v-model="formData.dataSource" multiple style="width: 100%;">
          <el-option label="OpenImages" value="OpenImages" />
          <el-option label="COCO Dataset" value="COCO" />
          <el-option label="BDD100K" value="BDD100K" />
          <el-option label="Mapillary" value="Mapillary" />
          <el-option label="TT100K" value="TT100K" />
          <el-option label="GoogleSpeechCommands" value="GoogleSpeechCommands" />
          <el-option label="LibriSpeech" value="LibriSpeech" />
          <el-option label="Kitti" value="Kitti" />
          <el-option label="内部数据库" value="InternalDB" />
          <el-option label="ImageNet" value="ImageNet" />
        </el-select>
      </el-form-item>
      <el-form-item label="目标补入数量">
        <el-input-number
          v-model="formData.targetCount"
          :min="1"
          :max="10000"
          :step="100"
          style="width: 100%;"
        />
      </el-form-item>
      <el-form-item label="相似度阈值">
        <el-slider v-model="formData.similarityThreshold" :min="0.5" :max="1.0" :step="0.05" show-input />
        <span class="param-hint">仅检索相似度高于此阈值的数据</span>
      </el-form-item>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { ref, watch, watchEffect } from 'vue';

interface Props {
  defectType: string;
  dataTypes: string[];
  strategyType: 'augmentation' | 'retrieval';
  modelValue: any;
}

const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue']);

const formData = ref({
  image: {
    noiseLevel: 50,
    blurRadius: 2,
    rotationAngle: 15,
    enableAdversarial: true,
  },
  text: {
    synonymReplaceRatio: 20,
    backTranslationLang: 'en-zh-en',
    enableParaphrase: true,
  },
  audio: {
    pitchShiftRange: 2,
    timeStretchRatio: 1.0,
    noiseSNR: 20,
  },
  dataSource: ['OpenImages'],
  targetCount: 1000,
  similarityThreshold: 0.75,
});

// 同步父组件传入的数据到 formData
watchEffect(() => {
  if (props.modelValue) {
    formData.value = { ...formData.value, ...props.modelValue };
  }
});

// 监听变化并向上传递
watch(formData, (val) => {
  emit('update:modelValue', val);
}, { deep: true });
</script>

<style scoped lang="scss">
.param-hint {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-divider) {
  margin: 24px 0;
}
</style>
