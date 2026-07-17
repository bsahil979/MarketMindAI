package com.example.ingestion_service.scheduler;

import com.example.ingestion_service.model.MarketData;
import com.example.ingestion_service.model.NewsSentimentData;
import com.example.ingestion_service.service.MockMarketApiService;
import com.example.ingestion_service.service.RawStorageService;
import com.example.ingestion_service.service.KafkaProducerService;
import lombok.Getter;
import lombok.Setter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

@Slf4j
@Component
public class IngestionScheduler {

    private final MockMarketApiService marketApiService;
    private final RawStorageService rawStorageService;
    private final KafkaProducerService kafkaProducerService;
    
    private final List<String> tickers = List.of("AAPL", "MSFT", "GOOGL", "AMZN", "TSLA");

    @Getter
    @Setter
    private boolean schedulerEnabled = true;

    @Getter
    private int processedPricesCount = 0;

    @Getter
    private int processedNewsCount = 0;

    public IngestionScheduler(MockMarketApiService marketApiService, RawStorageService rawStorageService, KafkaProducerService kafkaProducerService) {
        this.marketApiService = marketApiService;
        this.rawStorageService = rawStorageService;
        this.kafkaProducerService = kafkaProducerService;
    }

    @Scheduled(fixedDelayString = "${marketmind.ingestion-interval-ms:30000}")
    public void runIngestion() {
        if (!schedulerEnabled) {
            log.info("Ingestion scheduler is currently disabled. Skipping run.");
            return;
        }
        triggerIngestionProcess();
    }

    public synchronized void triggerIngestionProcess() {
        log.info("Starting market data ingestion process for tickers: {}", tickers);
        
        try {
            // Fetch and publish market prices via Kafka (fallback to direct raw storage if broker offline)
            List<MarketData> prices = marketApiService.fetchMarketData(tickers);
            for (MarketData price : prices) {
                try {
                    kafkaProducerService.sendMarketPrice(price);
                    processedPricesCount++;
                } catch (Exception e) {
                    log.warn("Kafka is offline. Running direct raw storage fallback for: {}", price.getTicker());
                    if (rawStorageService.saveMarketPrice(price)) {
                        processedPricesCount++;
                    }
                }
            }
            log.info("Successfully ingested {} stock price updates", prices.size());

            // Fetch and publish news sentiment via Kafka
            List<NewsSentimentData> news = marketApiService.fetchNewsSentiment(tickers);
            for (NewsSentimentData item : news) {
                try {
                    kafkaProducerService.sendNewsSentiment(item);
                    processedNewsCount++;
                } catch (Exception e) {
                    log.warn("Kafka is offline. Running direct raw storage fallback for news: {}", item.getTicker());
                    if (rawStorageService.saveNewsSentiment(item)) {
                        processedNewsCount++;
                    }
                }
            }
            log.info("Successfully ingested {} stock news updates", news.size());

        } catch (Exception e) {
            log.error("Exception occurred during scheduled ingestion process", e);
        }
    }
}
