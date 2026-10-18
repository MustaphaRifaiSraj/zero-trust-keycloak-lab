package com.acme.keycloak;

import java.util.List;
import org.keycloak.Config;
import org.keycloak.authentication.Authenticator;
import org.keycloak.authentication.AuthenticatorFactory;
import org.keycloak.models.AuthenticationExecutionModel;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;
import org.keycloak.provider.ProviderConfigProperty;

/** Tells Keycloak this plug-in exists, what it is called and which settings it has. */
public class BusinessHoursAuthenticatorFactory implements AuthenticatorFactory {

    public static final String PROVIDER_ID = "business-hours-check";
    public static final String START_HOUR = "startHour";
    public static final String END_HOUR = "endHour";
    public static final String TIMEZONE = "timezone";

    private static final Authenticator INSTANCE = new BusinessHoursAuthenticator();

    private static final List<ProviderConfigProperty> CONFIG = List.of(
            new ProviderConfigProperty(START_HOUR, "Start hour (0-24)",
                    "First hour of the day when login is allowed", ProviderConfigProperty.STRING_TYPE, "8"),
            new ProviderConfigProperty(END_HOUR, "End hour (0-24)",
                    "Login is blocked from this hour onward", ProviderConfigProperty.STRING_TYPE, "18"),
            new ProviderConfigProperty(TIMEZONE, "Time zone",
                    "Time zone name such as UTC or Europe/London", ProviderConfigProperty.STRING_TYPE, "UTC"));

    private static final AuthenticationExecutionModel.Requirement[] REQUIREMENTS = {
            AuthenticationExecutionModel.Requirement.REQUIRED,
            AuthenticationExecutionModel.Requirement.DISABLED
    };

    @Override
    public String getId() {
        return PROVIDER_ID;
    }

    @Override
    public String getDisplayType() {
        return "Business Hours Check";
    }

    @Override
    public String getReferenceCategory() {
        return "business-hours";
    }

    @Override
    public boolean isConfigurable() {
        return true;
    }

    @Override
    public AuthenticationExecutionModel.Requirement[] getRequirementChoices() {
        return REQUIREMENTS;
    }

    @Override
    public boolean isUserSetupAllowed() {
        return false;
    }

    @Override
    public String getHelpText() {
        return "Allows login only between a start hour and an end hour.";
    }

    @Override
    public List<ProviderConfigProperty> getConfigProperties() {
        return CONFIG;
    }

    @Override
    public Authenticator create(KeycloakSession session) {
        return INSTANCE;
    }

    @Override
    public void init(Config.Scope config) {
    }

    @Override
    public void postInit(KeycloakSessionFactory factory) {
    }

    @Override
    public void close() {
    }
}
