package com.example.ingestion_service.service;

import com.example.ingestion_service.model.MarketData;
import com.example.ingestion_service.model.NewsSentimentData;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class KafkaProducerService {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    public KafkaProducerService(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendMarketPrice(MarketData data) {
        try {
            log.info("Producing market price update to Kafka for {}: {}", data.getTicker(), data.getClose());
            kafkaTemplate.send("marketmind-prices", data.getTicker(), data);
        } catch (Exception e) {
            log.warn("Failed to send market price update to Kafka for " + data.getTicker() + ". Kafka may be offline: " + e.getMessage());
        }
    }

    public void sendNewsSentiment(NewsSentimentData data) {
        try {
            log.info("Producing news sentiment update to Kafka for {}: {}", data.getTicker(), data.getTitle());
            kafkaTemplate.send("marketmind-news", data.getTicker(), data);
        } catch (Exception e) {
            log.warn("Failed to send news sentiment update to Kafka for " + data.getTicker() + ". Kafka may be offline: " + e.getMessage());
        }
    }
}
