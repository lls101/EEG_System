
import { computed, effectScope, onScopeDispose, ref, watch } from 'vue';
import Plotly from 'plotly.js-dist-min';
import { useElementSize } from '@vueuse/core';
import { useThemeStore } from '@/store/modules/theme';

/**
 * A composable function to use Plotly.js
 *
 * @param initialData Factory function for initial plot data
 * @param initialLayout Factory function for initial plot layout
 * @param initialConfig Factory function for initial plot config
 */
export function usePlotly(
  initialData: () => Plotly.Data[],
  initialLayout: () => Partial<Plotly.Layout>,
  initialConfig: () => Partial<Plotly.Config>
) {
  const scope = effectScope();

  const themeStore = useThemeStore();
  const darkMode = computed(() => themeStore.darkMode);

  const domRef = ref<HTMLElement | null>(null);
  const { width, height } = useElementSize(domRef);

  const isInitialized = ref(false);

  /**
   * The core function to draw or update the plot.
   * Plotly.react is efficient and will update the existing plot if possible.
   */
  const react = () => {
    if (!domRef.value) return;

    const data = initialData();
    const layout = initialLayout();
    const config = initialConfig();

    // Apply theme-aware colors
    if (darkMode.value) {
      layout.paper_bgcolor = '#101014';
      layout.plot_bgcolor = '#101014';
      layout.font = { ...layout.font, color: '#e0e0e0' };
      // You can add more dark-theme specific layout adjustments here
    } else {
      layout.paper_bgcolor = '#ffffff';
      layout.plot_bgcolor = '#ffffff';
      layout.font = { ...layout.font, color: '#1f1f1f' };
    }

    Plotly.react(domRef.value, data, layout, config);
    isInitialized.value = true;
  };

  // Watch for container size changes and update layout
  watch([width, height], ([newWidth, newHeight]) => {
    if (isInitialized.value && domRef.value) {
      Plotly.relayout(domRef.value, { width: newWidth, height: newHeight });
    }
  });

  // Watch for theme changes and redraw the plot
  watch(darkMode, () => {
    if (isInitialized.value) {
      react();
    }
  });

  // Initial render
  watch(
    () => domRef.value,
    newValue => {
      if (newValue && !isInitialized.value) {
        react();
      }
    }
  );

  // Cleanup when the component is unmounted
  onScopeDispose(() => {
    if (domRef.value) {
      Plotly.purge(domRef.value);
    }
    scope.stop();
  });

  return {
    domRef,
    react
  };
}
