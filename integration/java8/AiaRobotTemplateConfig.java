package integration.java8;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

public class AiaRobotTemplateConfig {
    private final Properties props;

    public AiaRobotTemplateConfig() {
        this.props = new Properties();
    }

    public static AiaRobotTemplateConfig fromFile(String path) throws IOException {
        if (path == null || path.trim().length() == 0) {
            throw new IllegalArgumentException("AIA robot template config file path is required");
        }
        FileInputStream in = new FileInputStream(path);
        try {
            return fromProperties(in);
        } finally {
            in.close();
        }
    }

    public static AiaRobotTemplateConfig fromProperties(InputStream input) throws IOException {
        if (input == null) {
            throw new IllegalArgumentException("AIA robot template config input is required");
        }
        AiaRobotTemplateConfig config = new AiaRobotTemplateConfig();
        config.props.load(input);
        return config;
    }

    public int classId(String classType, int fallback) {
        return number("aia.class." + cleanKey(classType), fallback);
    }

    public int[] items(String classType) {
        String specific = text("aia.item." + cleanKey(classType), "");
        if (specific.length() > 0) {
            return intList(specific);
        }
        return intList(text("aia.item.default", ""));
    }

    public int[] skills(String classType) {
        String specific = text("aia.skill." + cleanKey(classType), "");
        if (specific.length() > 0) {
            return intList(specific);
        }
        return intList(text("aia.skill.default", ""));
    }

    public int spawnHp(String classType, int fallback) {
        String key = "aia.hp." + cleanKey(classType);
        return number(key, number("aia.hp.default", fallback));
    }

    public int spawnMp(String classType, int fallback) {
        String key = "aia.mp." + cleanKey(classType);
        return number(key, number("aia.mp.default", fallback));
    }

    public String namePrefix(String classType, String fallback) {
        String key = "aia.namePrefix." + cleanKey(classType);
        String value = text(key, "");
        if (value.length() > 0) {
            return value;
        }
        return text("aia.namePrefix.default", fallback == null ? "AIA" : fallback);
    }

    public String raw(String key, String fallback) {
        return text(key, fallback);
    }

    private String text(String key, String fallback) {
        String value = props.getProperty(key);
        if (value == null || value.trim().length() == 0) {
            return fallback;
        }
        return value.trim();
    }

    private int number(String key, int fallback) {
        String value = props.getProperty(key);
        if (value == null || value.trim().length() == 0) {
            return fallback;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (Exception ignored) {
            return fallback;
        }
    }

    private int[] intList(String value) {
        if (value == null || value.trim().length() == 0) {
            return new int[0];
        }
        String[] parts = value.split(",");
        int[] temp = new int[parts.length];
        int count = 0;
        for (int i = 0; i < parts.length; i++) {
            String part = parts[i] == null ? "" : parts[i].trim();
            if (part.length() == 0) {
                continue;
            }
            try {
                temp[count++] = Integer.parseInt(part);
            } catch (Exception ignored) {
                // Ignore malformed ids so one bad item does not break server boot.
            }
        }
        int[] result = new int[count];
        System.arraycopy(temp, 0, result, 0, count);
        return result;
    }

    private String cleanKey(String value) {
        if (value == null || value.trim().length() == 0) {
            return "default";
        }
        return value.trim().toLowerCase();
    }
}
