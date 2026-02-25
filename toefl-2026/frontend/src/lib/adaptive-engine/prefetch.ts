// Pre-Fetch Buffer Logic to achieve 0-ms latency between Stage 1 and Stage 2

export interface Stage2Assets {
    track: 'Track A' | 'Track B';
    assetUrls: string[]; // JSON bundles, .mp3 audio, .mp4 video clips
}

export class MSTPrefetchBuffer {
    /**
     * Called when the user completes ~80% of Stage 1.
     * Silently downloads both Track A and Track B into the browser Cache API.
     */
    static async prefetchStage2Assets(assets: Stage2Assets[]): Promise<void> {
        if (!('caches' in window)) {
            console.warn("Cache API not supported in this browser.");
            return;
        }

        try {
            const cache = await caches.open('ets_mst_stage2_buffer');

            for (const trackAssets of assets) {
                // Background fetch
                this.fetchAndCache(cache, trackAssets.assetUrls);
            }
        } catch (error) {
            console.error("Failed to initialize pre-fetch buffer:", error);
        }
    }

    private static async fetchAndCache(cache: Cache, urls: string[]): Promise<void> {
        for (const url of urls) {
            try {
                const response = await cache.match(url);
                if (!response) {
                    await cache.add(url);
                    console.debug(`Prefetched asset: ${url}`);
                }
            } catch (err) {
                // Silently fail without interrupting the test execution
                console.warn(`Failed to prefetch ${url}:`, err);
            }
        }
    }

    /**
     * Called at the end of the test to evict test materials from the cache
     * complying with test security cleanup protocols.
     */
    static async clearBuffer(): Promise<void> {
        if ('caches' in window) {
            await caches.delete('ets_mst_stage2_buffer');
        }
    }
}
