/*************************************************************************
 * Copyright 2009-2013 Eucalyptus Systems, Inc.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses/.
 *
 * Please contact Eucalyptus Systems, Inc., 6755 Hollister Ave., Goleta
 * CA 93117, USA or visit http://www.eucalyptus.com/licenses/ if you need
 * additional information or have any questions.
 ************************************************************************/
package com.eucalyptus.tests.awssdk;

import com.amazonaws.services.identitymanagement.model.*;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import static com.eucalyptus.tests.awssdk.Eutester4j.*;

/**
 * This application tests management of IAM instance profiles.
 * <p/>
 * This is verification for the story:
 * <p/>
 * https://eucalyptus.atlassian.net/browse/EUCA-5404
 */
public class TestIAMInstanceProfileManagement {

    @Test
    public void IAMInstanceProfileManagementTest() throws Exception {
        testInfo(this.getClass().getSimpleName());
        getCloudInfo();
        final List<Runnable> cleanupTasks = new ArrayList<Runnable>();
        try {
            // Create instance profile
            final String profileName = NAME_PREFIX + "ProfileTest";
            print("Creating instance profile: " + profileName);
            youAre.createInstanceProfile(new CreateInstanceProfileRequest()
                    .withInstanceProfileName(profileName)
                    .withPath("/path"));
            cleanupTasks.add(new Runnable() {
                @Override
                public void run() {
                    print("Deleting instance profile: " + profileName);
                    youAre.deleteInstanceProfile(new DeleteInstanceProfileRequest()
                            .withInstanceProfileName(profileName));
                }
            });

            // Get instance profile
            print("Getting instance profile: " + profileName);
            {
                final GetInstanceProfileResult getProfileResult =
                        youAre.getInstanceProfile(new GetInstanceProfileRequest()
                                .withInstanceProfileName(profileName));
                assertThat(getProfileResult.getInstanceProfile() != null, "Expected profile");
                assertThat(profileName.equals(getProfileResult.getInstanceProfile().getInstanceProfileName()), "Unexpected profile name");
                assertThat("/path/".equals(getProfileResult.getInstanceProfile().getPath()), "Unexpected profile path");
                assertThat(getProfileResult.getInstanceProfile().getRoles() == null || getProfileResult.getInstanceProfile().getRoles().isEmpty(), "Unexpected roles");
            }

            // List instance profiles
            print("Listing instance profiles to verify profile present: " + profileName);
            {
                final ListInstanceProfilesResult listProfilesResult = youAre.listInstanceProfiles();
                boolean foundProfile = isProfilePresent(profileName, listProfilesResult.getInstanceProfiles());
                assertThat(foundProfile, "Profile not found in listing");
            }

            // List instance profiles with path
            print("Listing instance profiles by path to verify profile present: " + profileName);
            {
                final ListInstanceProfilesResult listProfilesResult =
                        youAre.listInstanceProfiles(new ListInstanceProfilesRequest().withPathPrefix("/path"));
                boolean foundProfile = isProfilePresent(profileName, listProfilesResult.getInstanceProfiles());
                assertThat(foundProfile, "Profile not found in listing for path");
            }

            // List instance profiles with non-matching path
            print("Listing instance profiles by path to verify profile not present: " + profileName);
            {
                final ListInstanceProfilesResult listProfilesResult =
                        youAre.listInstanceProfiles(new ListInstanceProfilesRequest()
                                .withPathPrefix("/---should-not-match-any-profiles---4ad1c6d3-bfdd-4dc8-8754-523b6624ce15"));
                boolean foundProfile = isProfilePresent(profileName, listProfilesResult.getInstanceProfiles());
                assertThat(!foundProfile, "Profile listed when path should not match");
            }

            // Create role
            final String roleName = NAME_PREFIX + "ProfileTest";
            print("Creating role: " + roleName);
            youAre.createRole(new CreateRoleRequest()
                    .withRoleName(roleName)
                    .withAssumeRolePolicyDocument(
                            "{\n" +
                                    "    \"Statement\": [ {\n" +
                                    "      \"Effect\": \"Allow\",\n" +
                                    "      \"Principal\": {\n" +
                                    "         \"Service\": [ \"ec2.amazonaws.com\" ]\n" +
                                    "      },\n" +
                                    "      \"Action\": [ \"sts:AssumeRole\" ]\n" +
                                    "    } ]\n" +
                                    "}"));
            cleanupTasks.add(new Runnable() {
                @Override
                public void run() {
                    print("Deleting role: " + roleName);
                    youAre.deleteRole(new DeleteRoleRequest()
                            .withRoleName(roleName));
                }
            });

            // Add role to instance profile
            print("Adding role: " + roleName + " to instance profile: " + profileName);
            youAre.addRoleToInstanceProfile(new AddRoleToInstanceProfileRequest()
                    .withInstanceProfileName(profileName)
                    .withRoleName(roleName));

            // Get instance profile (check role present)
            print("Getting instance profile:" + profileName + " to check for role: " + roleName);
            {
                final GetInstanceProfileResult getProfileResult =
                        youAre.getInstanceProfile(new GetInstanceProfileRequest()
                                .withInstanceProfileName(profileName));
                assertThat(getProfileResult.getInstanceProfile() != null, "Expected profile");
                assertThat(profileName.equals(getProfileResult.getInstanceProfile().getInstanceProfileName()), "Unexpected profile name");
                assertThat(getProfileResult.getInstanceProfile().getRoles() != null && getProfileResult.getInstanceProfile().getRoles().size() == 1, "Expected one role");
                assertThat(roleName.equals(getProfileResult.getInstanceProfile().getRoles().get(0).getRoleName()), "Unexpected role name");
            }

            // List instance profiles for role
            print("Listing instance profiles for role: " + roleName);
            {
                final ListInstanceProfilesForRoleResult listProfilesResult =
                        youAre.listInstanceProfilesForRole(new ListInstanceProfilesForRoleRequest()
                                .withRoleName(roleName));
                boolean foundProfile = isProfilePresent(profileName, listProfilesResult.getInstanceProfiles());
                assertThat(foundProfile, "Profile not found in listing for role");
            }

            // Remove role from instance profile
            print("Removing role: " + roleName + " from instance profile: " + profileName);
            youAre.removeRoleFromInstanceProfile(new RemoveRoleFromInstanceProfileRequest()
                    .withInstanceProfileName(profileName)
                    .withRoleName(roleName));

            // Get instance profile (check role removed)
            print("Getting instance profile:" + profileName + " to check role removed: " + roleName);
            {
                final GetInstanceProfileResult getProfileResult =
                        youAre.getInstanceProfile(new GetInstanceProfileRequest()
                                .withInstanceProfileName(profileName));
                assertThat(getProfileResult.getInstanceProfile() != null, "Expected profile");
                assertThat(profileName.equals(getProfileResult.getInstanceProfile().getInstanceProfileName()), "Unexpected profile name");
                assertThat(getProfileResult.getInstanceProfile().getRoles() == null || getProfileResult.getInstanceProfile().getRoles().isEmpty(), "Unexpected roles");
            }

            // Delete instance profile
            print("Deleting instance profile: " + profileName);
            youAre.deleteInstanceProfile(new DeleteInstanceProfileRequest()
                    .withInstanceProfileName(profileName));

            // List instance profiles (check deleted)
            print("Listing instance profiles to check deletion of profile: " + profileName);
            {
                final ListInstanceProfilesResult listProfilesResult = youAre.listInstanceProfiles();
                boolean foundProfile = isProfilePresent(profileName, listProfilesResult.getInstanceProfiles());
                assertThat(!foundProfile, "Profile found in listing after deletion");
            }

            print("Test complete");
        } finally {
            // Attempt to clean up anything we created
            Collections.reverse(cleanupTasks);
            for (final Runnable cleanupTask : cleanupTasks) {
                try {
                    cleanupTask.run();
                } catch (NoSuchEntityException e) {
                    print("Entity not found during cleanup.");
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }
    }

    private boolean isProfilePresent(final String profileName, final List<InstanceProfile> profiles) {
        boolean foundProfile = false;
        if (profiles != null) for (final InstanceProfile profile : profiles) {
            foundProfile = foundProfile || profileName.equals(profile.getInstanceProfileName());
        }
        return foundProfile;
    }
}
