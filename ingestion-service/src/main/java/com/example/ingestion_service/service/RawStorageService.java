package com.example.ingestion_service.service;

import com.example.ingestion_service.model.MarketData;
import com.example.ingestion_service.model.NewsSentimentData;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.format.DateTimeFormatter;

@Slf4j
@Service
public class RawStorageService {

    @Value("${marketmind.raw-storage-path}")
    private String baseStoragePath;

    private final ObjectMapper objectMapper;
    private final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss_SSS");

    public RawStorageService() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        this.objectMapper.configure(com.fasterxml.jackson.databind.SerializationFeature.WRITE_DATES_AS_TIMESTAMPS, false);
    }

    @PostConstruct
    public void init() {
        try {
            Files.createDirectories(Paths.get(baseStoragePath, "prices"));
            Files.createDirectories(Paths.get(baseStoragePath, "news"));
            log.info("Initialized raw storage directories at: {}", Paths.get(baseStoragePath).toAbsolutePath());
        } catch (IOException e) {
            log.error("Failed to create raw storage directories", e);
        }
    }

    public boolean saveMarketPrice(MarketData data) {
        try {
            String timestampStr = data.getTimestamp().format(formatter);
            String filename = String.format("%s_%s.json", data.getTicker(), timestampStr);
            Path filePath = Paths.get(baseStoragePath, "prices", filename);
            
            objectMapper.writeValue(filePath.toFile(), data);
            log.debug("Saved raw market price for {} to {}", data.getTicker(), filePath.getFileName());
            return true;
        } catch (IOException e) {
            log.error("Error saving raw market price for {}", data.getTicker(), e);
            return false;
        }
    }

    public boolean saveNewsSentiment(NewsSentimentData data) {
        try {
            String timestampStr = data.getTimestamp().format(formatter);
            String filename = String.format("%s_%s.json", data.getTicker(), timestampStr);
            Path filePath = Paths.get(baseStoragePath, "news", filename);
            
            objectMapper.writeValue(filePath.toFile(), data);
            log.debug("Saved raw news sentiment for {} to {}", data.getTicker(), filePath.getFileName());
            return true;
        } catch (IOException e) {
            log.error("Error saving raw news sentiment for {}", data.getTicker(), e);
            return false;
        }
    }
}
