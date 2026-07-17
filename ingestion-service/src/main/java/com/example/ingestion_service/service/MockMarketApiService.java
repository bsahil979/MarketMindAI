package com.example.ingestion_service.service;

import com.example.ingestion_service.model.MarketData;
import com.example.ingestion_service.model.NewsSentimentData;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.LocalDateTime;
import java.util.*;
import java.util.logging.Logger;

@Service
public class MockMarketApiService {

    private static final Logger LOGGER = Logger.getLogger(MockMarketApiService.class.getName());
    private final Random random = new Random();
    private final Map<String, Double> baselinePrices = new HashMap<>();
    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    public MockMarketApiService() {
        // Initialize base prices for mock tickers
        baselinePrices.put("AAPL", 185.0);
        baselinePrices.put("MSFT", 420.0);
        baselinePrices.put("GOOGL", 175.0);
        baselinePrices.put("AMZN", 180.0);
        baselinePrices.put("TSLA", 240.0);
    }

    public List<MarketData> fetchMarketData(List<String> tickers) {
        List<MarketData> result = new ArrayList<>();
        LocalDateTime now = LocalDateTime.now();

        for (String ticker : tickers) {
            MarketData data = fetchFromYahooFinance(ticker, now);
            if (data != null) {
                result.add(data);
                // Update local baseline in case fallback is needed next time
                baselinePrices.put(ticker, data.getClose());
            } else {
                // FALLBACK to mock data
                result.add(generateMockMarketData(ticker, now));
            }
        }
        return result;
    }

    private MarketData fetchFromYahooFinance(String ticker, LocalDateTime now) {
        try {
            String url = "https://query1.finance.yahoo.com/v8/finance/chart/" + ticker + "?range=1d&interval=1m";
            
            HttpHeaders headers = new HttpHeaders();
            headers.set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
            HttpEntity<String> entity = new HttpEntity<>(headers);
            
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, entity, String.class);
            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                JsonNode root = objectMapper.readTree(response.getBody());
                JsonNode resultNode = root.path("chart").path("result").get(0);
                if (resultNode != null) {
                    JsonNode meta = resultNode.path("meta");
                    double close = meta.path("regularMarketPrice").asDouble();
                    double prevClose = meta.path("chartPreviousClose").asDouble();
                    
                    JsonNode quote = resultNode.path("indicators").path("quote").get(0);
                    double open = quote.path("open").get(0).asDouble(close);
                    double high = quote.path("high").get(0).asDouble(close);
                    double low = quote.path("low").get(0).asDouble(close);
                    long volume = quote.path("volume").get(0).asLong(5000000);
                    
                    LOGGER.info("Successfully fetched real-time market data for " + ticker + " from Yahoo Finance. Price: " + close);
                    return MarketData.builder()
                            .ticker(ticker)
                            .open(round(open))
                            .high(round(high))
                            .low(round(low))
                            .close(round(close))
                            .volume(volume)
                            .timestamp(now)
                            .build();
                }
            }
        } catch (Exception e) {
            LOGGER.warning("Failed to fetch data from Yahoo Finance for " + ticker + ": " + e.getMessage() + ". Using fallback.");
        }
        return null;
    }

    private MarketData generateMockMarketData(String ticker, LocalDateTime now) {
        double base = baselinePrices.getOrDefault(ticker, 100.0);
        // Simulate random price walk (+/- 1.5%)
        double percentChange = (random.nextDouble() * 3.0 - 1.5) / 100.0;
        double close = base * (1 + percentChange);
        baselinePrices.put(ticker, close); // update baseline

        double open = close * (1 + (random.nextDouble() * 0.4 - 0.2) / 100.0);
        double high = Math.max(open, close) * (1 + (random.nextDouble() * 0.3) / 100.0);
        double low = Math.min(open, close) * (1 - (random.nextDouble() * 0.3) / 100.0);
        long volume = 1000000 + random.nextInt(9000000);

        return MarketData.builder()
                .ticker(ticker)
                .open(round(open))
                .high(round(high))
                .low(round(low))
                .close(round(close))
                .volume(volume)
                .timestamp(now)
                .build();
    }

    public List<NewsSentimentData> fetchNewsSentiment(List<String> tickers) {
        List<NewsSentimentData> result = new ArrayList<>();
        LocalDateTime now = LocalDateTime.now();

        String[] headlines = {
            "earnings report beats analyst estimates",
            "announces new product expansion plans",
            "faces supply chain hurdles amid regulatory scrutiny",
            "unveils breakthrough AI integration technology",
            "stock rises after positive analyst upgrades"
        };

        String[] sources = {"Bloomberg", "Reuters", "TechCrunch", "CNBC", "WSJ"};

        for (String ticker : tickers) {
            // 40% chance of generating a news item per ticker to simulate realistic updates
            if (random.nextDouble() < 0.4) {
                int headlineIdx = random.nextInt(headlines.length);
                int sourceIdx = random.nextInt(sources.length);
                
                String title = ticker + " " + headlines[headlineIdx];
                String url = "https://mockfinanceapi.com/news/" + ticker.toLowerCase() + "_" + System.currentTimeMillis();
                
                // Sentiment score between -1.00 and +1.00
                double sentimentScore = random.nextDouble() * 2.0 - 1.0;
                // Confidence score between 0.50 and 1.00
                double confidenceScore = 0.5 + random.nextDouble() * 0.5;

                result.add(NewsSentimentData.builder()
                        .ticker(ticker)
                        .title(title)
                        .url(url)
                        .source(sources[sourceIdx])
                        .sentimentScore(round(sentimentScore))
                        .confidenceScore(round(confidenceScore))
                        .timestamp(now)
                        .build());
            }
        }
        return result;
    }

    private double round(double value) {
        return Math.round(value * 10000.0) / 10000.0;
    }
}
