package com.acme.keycloak;

import jakarta.ws.rs.core.Response;
import java.time.DateTimeException;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Map;
import org.keycloak.authentication.AuthenticationFlowContext;
import org.keycloak.authentication.AuthenticationFlowError;
import org.keycloak.authentication.Authenticator;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.RealmModel;
import org.keycloak.models.UserModel;

/** Lets a login continue only between a start hour and an end hour. */
public class BusinessHoursAuthenticator implements Authenticator {

    @Override
    public void authenticate(AuthenticationFlowContext context) {
        int startHour = 8;
        int endHour = 18;
        String timezone = "UTC";

        // Read the values an administrator typed into the settings screen (if any).
        if (context.getAuthenticatorConfig() != null && context.getAuthenticatorConfig().getConfig() != null) {
            Map<String, String> config = context.getAuthenticatorConfig().getConfig();
            startHour = readHour(config.get(BusinessHoursAuthenticatorFactory.START_HOUR), startHour);
            endHour = readHour(config.get(BusinessHoursAuthenticatorFactory.END_HOUR), endHour);
            String configuredZone = config.get(BusinessHoursAuthenticatorFactory.TIMEZONE);
            if (configuredZone != null && !configuredZone.isBlank()) {
                timezone = configuredZone.trim();
            }
        }

        ZonedDateTime now;
        try {
            now = ZonedDateTime.now(ZoneId.of(timezone));
        } catch (DateTimeException e) {
            timezone = "UTC"; // unknown time zone name: fall back to UTC
            now = ZonedDateTime.now(ZoneId.of("UTC"));
        }

        int hour = now.getHour();
        if (hour >= startHour && hour < endHour) {
            context.success(); // inside business hours: let the login continue
            return;
        }

        // Outside business hours: stop the login and show a clear message.
        Response errorPage = context.form()
                .setError("Login is only allowed between " + startHour + ":00 and " + endHour
                        + ":00 (" + timezone + "). Please try again during business hours.")
                .createErrorPage(Response.Status.FORBIDDEN);
        context.failure(AuthenticationFlowError.ACCESS_DENIED, errorPage);
    }

    private int readHour(String value, int fallback) {
        try {
            int hour = Integer.parseInt(value.trim());
            return (hour >= 0 && hour <= 24) ? hour : fallback;
        } catch (Exception e) {
            return fallback;
        }
    }

    @Override
    public void action(AuthenticationFlowContext context) {
        // Nothing to do: this step never shows a form.
    }

    @Override
    public boolean requiresUser() {
        return false; // the check does not depend on who is logging in
    }

    @Override
    public boolean configuredFor(KeycloakSession session, RealmModel realm, UserModel user) {
        return true;
    }

    @Override
    public void setRequiredActions(KeycloakSession session, RealmModel realm, UserModel user) {
        // Nothing to do.
    }

    @Override
    public void close() {
        // Nothing to clean up.
    }
}
