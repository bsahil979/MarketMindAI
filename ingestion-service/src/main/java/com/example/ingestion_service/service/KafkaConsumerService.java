package com.example.ingestion_service.service;

import com.example.ingestion_service.model.MarketData;
import com.example.ingestion_service.model.NewsSentimentData;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class KafkaConsumerService {

    private final RawStorageService rawStorageService;

    public KafkaConsumerService(RawStorageService rawStorageService) {
        this.rawStorageService = rawStorageService;
    }

    @KafkaListener(topics = "marketmind-prices", groupId = "marketmind-ingest-group")
    public void consumeMarketPrice(MarketData data) {
        log.info("Received market price event from Kafka for {}: {}", data.getTicker(), data.getClose());
        try {
            boolean success = rawStorageService.saveMarketPrice(data);
            if (success) {
                log.info("Successfully persisted Kafka market price event for " + data.getTicker() + " to raw storage");
            }
        } catch (Exception e) {
            log.error("Failed to persist Kafka market price event for " + data.getTicker() + ": " + e.getMessage());
        }
    }

    @KafkaListener(topics = "marketmind-news", groupId = "marketmind-ingest-group")
    public void consumeNewsSentiment(NewsSentimentData data) {
        log.info("Received news sentiment event from Kafka for {}: {}", data.getTicker(), data.getTitle());
        try {
            boolean success = rawStorageService.saveNewsSentiment(data);
            if (success) {
                log.info("Successfully persisted Kafka news sentiment event for " + data.getTicker() + " to raw storage");
            }
        } catch (Exception e) {
            log.error("Failed to persist Kafka news sentiment event for " + data.getTicker() + ": " + e.getMessage());
        }
    }
}
